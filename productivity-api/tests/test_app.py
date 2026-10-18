def signup(client, username="echo", password="secret123"):
    return client.post("/signup", json={"username": username, "password": password})


def make_note(client, title="Groceries", content="milk and eggs"):
    return client.post("/notes", json={"title": title, "content": content})


class TestAuth:
    def test_signup_logs_user_in(self, client):
        res = signup(client)
        assert res.status_code == 201
        assert res.get_json()["username"] == "echo"
        assert "password" not in str(res.get_json())
        assert client.get("/check_session").status_code == 200
        assert client.get("/me").status_code == 200

    def test_signup_rejects_duplicate_and_short_password(self, client):
        signup(client)
        assert signup(client).status_code == 422
        assert signup(client, "other", "123").status_code == 422
        assert signup(client, "other", "      ").status_code == 422
        assert signup(client, "u" * 51, "secret123").status_code == 422
        assert client.post("/signup", json={"password": "secret123"}).status_code == 422

    def test_usernames_are_case_insensitive(self, client):
        signup(client, "Echo")
        assert signup(client, "echo").status_code == 422
        client.delete("/logout")
        res = client.post("/login", json={"username": "ECHO", "password": "secret123"})
        assert res.status_code == 200
        assert res.get_json()["username"] == "echo"

    def test_non_json_body_is_rejected(self, client):
        res = client.post("/signup", data="not json", content_type="text/plain")
        assert res.status_code == 400

    def test_login_and_logout(self, client):
        signup(client)
        client.delete("/logout")
        assert client.get("/check_session").status_code == 401

        bad = client.post("/login", json={"username": "echo", "password": "nope"})
        assert bad.status_code == 401

        ok = client.post("/login", json={"username": "echo", "password": "secret123"})
        assert ok.status_code == 200
        assert client.delete("/logout").status_code == 204
        assert client.delete("/logout").status_code == 401

    def test_password_is_hashed(self, client):
        from models import User

        signup(client)
        user = User.query.first()
        assert user._password_hash != "secret123"
        assert user.authenticate("secret123")


class TestNotes:
    def test_routes_need_login(self, client):
        assert client.get("/notes").status_code == 401
        assert make_note(client).status_code == 401
        assert client.patch("/notes/1", json={"title": "x"}).status_code == 401
        assert client.delete("/notes/1").status_code == 401

    def test_crud(self, client):
        signup(client)
        created = make_note(client)
        assert created.status_code == 201
        note_id = created.get_json()["id"]

        patched = client.patch(f"/notes/{note_id}", json={"title": "Shopping"})
        assert patched.status_code == 200
        assert patched.get_json()["title"] == "Shopping"
        assert patched.get_json()["content"] == "milk and eggs"

        assert client.delete(f"/notes/{note_id}").status_code == 204
        assert client.get(f"/notes/{note_id}").status_code == 404

    def test_validation(self, client):
        signup(client)
        assert client.post("/notes", json={"title": "", "content": "x"}).status_code == 422
        assert client.post("/notes", json={"title": "x"}).status_code == 422

    def test_client_cannot_set_owner(self, client):
        signup(client, "echo")
        res = client.post("/notes", json={"title": "a", "content": "b", "user_id": 999})
        assert res.get_json()["user_id"] == 1

    def test_per_page_is_capped(self, client):
        signup(client)
        assert client.get("/notes?per_page=1000").get_json()["per_page"] == 50

    def test_pagination(self, client):
        signup(client)
        for i in range(7):
            make_note(client, title=f"note {i}")
        page1 = client.get("/notes?page=1&per_page=3").get_json()
        assert len(page1["notes"]) == 3
        assert page1["total"] == 7
        assert page1["pages"] == 3
        page3 = client.get("/notes?page=3&per_page=3").get_json()
        assert len(page3["notes"]) == 1
        assert client.get("/notes?page=99").get_json()["notes"] == []

    def test_users_cannot_touch_each_others_notes(self, client):
        signup(client, "echo")
        note_id = make_note(client).get_json()["id"]
        client.delete("/logout")

        signup(client, "amanda")
        assert client.get("/notes").get_json()["total"] == 0
        assert client.get(f"/notes/{note_id}").status_code == 403
        assert client.patch(f"/notes/{note_id}", json={"title": "hacked"}).status_code == 403
        assert client.delete(f"/notes/{note_id}").status_code == 403

    def test_patch_validation(self, client):
        signup(client)
        note_id = make_note(client).get_json()["id"]
        assert client.patch(f"/notes/{note_id}", json={"title": ""}).status_code == 422
        assert client.patch(f"/notes/{note_id}", json={"title": "   "}).status_code == 422
        assert client.patch(f"/notes/{note_id}", json={"title": "x" * 101}).status_code == 422

    def test_patch_and_delete_nonexistent(self, client):
        signup(client)
        assert client.patch("/notes/9999", json={"title": "Missing"}).status_code == 404
        assert client.delete("/notes/9999").status_code == 404

