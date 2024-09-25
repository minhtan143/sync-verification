import os, requests, psycopg2, logging

output = "id_card/"
data = []


def getAllIdCard():
    conn = psycopg2.connect(
        database="identity",
        host="host.docker.internal",
        user="postgres",
        password="example",
        port="39797",
    )

    cursor = conn.cursor()
    cursor.execute(
        """
            SELECT us."phoneNumber", ic."idCardFront", ic."idCardBack", us."hash"
            FROM "id_card" ic
	            LEFT JOIN "user" us ON ic."userId" = us."id"
        """
    )

    global data
    data = cursor.fetchall()
    for card in data:
        print(f"Get verification of {card[0]}")
        os.makedirs(os.path.dirname(output), exist_ok=True)
        store = output + card[0]

        idCardFront = requests.get(card[1]).content
        open(store + "_front_idcard.jpg", "wb").write(idCardFront)

        idCardBack = requests.get(card[2]).content
        open(store + "_back_idcard.jpg", "wb").write(idCardBack)


def postAllIdCard():
    for user in data:
        # login
        response = requests.post(
            "https://buyer.host.docker.internal:39791/connect/token",
            headers={"Content-Length": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "password",
                "scope": "yocar",
                "client_id": "yocar_App",
                "username": user[0],
                "password": user[3],
            },
            verify=False,
        )

        if response.status_code != 200:
            logging.exception(
                f"------------- Can't logging to {user[0]}: {response.json()}"
            )
            continue

        print(f"Logging in {user[0]}")
        token = response.json()["access_token"]

        # update
        files = {
            "idCardFront": open(f"{output}{user[0]}_front_idcard.jpg", "rb"),
            "idCardBack": open(f"{output}{user[0]}_back_idcard.jpg", "rb"),
        }

        response = requests.post(
            "https://host.docker.internal:39793/api/v2/identity/users/buyer/me/verification",
            headers={
                "Content-Length": "multipart/form-data",
                "Authorization": f"Bearer {token}",
            },
            files=files,
            verify=False,
        )

        if response.status_code != 200:
            logging.exception(
                f"------------- Can't update verification to {user[0]}: {response.json()}"
            )
            continue

        print(f"Updated verification for {user[0]}")


def sync():
    getAllIdCard()
    postAllIdCard()
