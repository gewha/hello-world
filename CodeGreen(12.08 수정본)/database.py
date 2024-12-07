import os
import pyrebase
import hashlib
import json

class DBhandler:
    def __init__(self):
        with open('./Authentication/firebase_auth.json') as f:
            config = json.load(f)
        firebase = pyrebase.initialize_app(config)
        self.db = firebase.database()

    def insert_item(self, product_id, product_data):
        try:
            self.db.child("items").child(product_id).set(product_data)
            print(f"Item {product_id} successfully inserted into Firebase.")
            return True
        except Exception as e:
            print(f"Error inserting item {product_id} into Firebase: {e}")
            return False

    def get_items(self):
        try:
            items = self.db.child("items").get()
            if items.val():
                print("Items successfully retrieved from Firebase.")
                return items.val()
            return {}
        except Exception as e:
            print(f"Error retrieving items from Firebase: {e}")
            return {}

    def get_item_by_id(self, product_id):
        try:
            item = self.db.child("items").child(product_id).get()
            if item.val():
                print(f"Item {product_id} successfully retrieved from Firebase.")
                return item.val()
            return None
        except Exception as e:
            print(f"Error retrieving item {product_id} from Firebase: {e}")
            return None

    def user_duplicate_check(self, email):
        users = self.db.child("users").get()
        print("users###", users.val())
        if str(users.val()) == "None":  # first registration
            return True
        else:
            for res in users.each():
                value = res.val()
                if value['email'] == email:
                    return False
            return True

    def insert_user(self, id, password, nickname, email, phone, role):
        user_data = {
            "id": id,
            "password": password,
            "nickname": nickname,
            "email": email,
            "phone": phone,
            "role": role
        }
        if self.user_duplicate_check(email):
            self.db.child("users").push(user_data)
            print(user_data)
            return True
        else:
            return False

    def find_user(self, id, password):
        users = self.db.child("users").get()
        target_value = []

        if not users.val():
            print("No users found")
            return None

        for res in users.each():
            value = res.val()
            print(f"Checking user: {value}")  # data 확인

            if 'id' in value and 'password' in value:
                if value['id'] == id and value['password'] == password:
                    return value  # 사용자 정보 반환
        return None
    
        
    def insert_review(self, review_id, review_data):
        try:
            self.db.child("reviews").child(review_id).set(review_data)
            print(f"Review {review_id} successfully inserted into Firebase.")
            return True
        except Exception as e:
            print(f"Error inserting item {review_id} into Firebase: {e}")
            return False
    
    def get_reviews(self):
        try:
            result = self.db.child("reviews").get()
            if result.val():
                print("reviews successfully retrieved from Firebase")
                return result.val()
            return {}
        except Exception as e:
            print(f"Error retrieving reviews from Firebase: {e}")
            return {}
        
    def get_review_by_id(self, review_id):
        try:
            reviews = self.db.child("reviews").get()
            target_value=""
            for review in reviews.each():
                key_value = review.key()
                if key_value == review_id:
                    target_value=review.val()
            return target_value
        except Exception as e:
            print(f"Error retrieving review {review_id} from Firebase: {e}")
            return None

    def get_review_by_nickname(self, nickname):
        try:
            reviews = self.db.child("reviews").order_by_child("user_nickname").equal_to(nickname).get()
            if reviews.val():
                print("reviews successfully retrieved from Firebase")
                return reviews.val()
            return {}
        except Exception as e:
            print(f"Error retrieving review {nickname} from Firebase: {e}")
            return None

    
    def get_heart_byname(self, uid, name):
        hearts = self.db.child("heart").child(uid).get()
        target_value = ""

        if hearts.val() is None:
            return target_value

        for res in hearts.each():
            key_value = res.key()
            if key_value == name:
                target_value = res.val()  # 해당 상품의 좋아요 상태
                return target_value

        return target_value

    def update_heart(self, user_id, isHeart, item):
        heart_info = {
            "interested": isHeart  # 좋아요 상태
        }
        
        self.db.child("heart").child(user_id).child(item).set(heart_info)
        return True
