import requests


BASE_URL = "http://127.0.0.1:5000"


def main():
    # 1) Просмотр списка новостей (доступно без прав)
    r = requests.get(f"{BASE_URL}/api/posts")
    print("Posts list:", r.status_code, r.json())

    # 2) Чтение одной новости
    post_id = int(input("Введите id новости для просмотра: ").strip() or "1")
    r = requests.get(f"{BASE_URL}/api/posts/{post_id}")
    print("Post id={post_id}:", r.status_code, r.json())

    # 3) Логин администратора (нужен для добавления/удаления новости)
    admin_session = requests.Session()
    admin_password = input("Введите пароль от admin: ").strip()
    r = admin_session.post(
        f"{BASE_URL}/api/auth/login",
        json={"username": "Whyiok", "password": admin_password},
    )
    print("admin login:", r.status_code, r.json())

    # 4) Добавление новости
    title = "API: новая новость"
    text = "Полный текст новости"
    r = admin_session.post(
        f"{BASE_URL}/api/posts",
        json={"title": title, "text": text},
    )
    print("create:", r.status_code, r.json())

    # 5) Удаление поста
    delete_id = int(input("Введите id поста для удаления: ").strip())
    r = admin_session.delete(f"{BASE_URL}/api/posts/{delete_id}")
    print("delete:", r.status_code, r.json())


if __name__ == "__main__":
    main()

