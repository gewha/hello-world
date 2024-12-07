import logging
from flask import Flask, render_template, request, flash, redirect, url_for, session, jsonify
from database import DBhandler
import os
import hashlib
import sys

app = Flask(__name__)
app.secret_key = 'super_secret_key'  # 세션 관리를 위한 키 설정

DB = DBhandler()

@app.before_request
def set_default_session_values():
    # 세션에 'role' 키가 없을 경우 기본값을 'Seller'로 설정
    if 'role' not in session:
        session['role'] = 'Seller'

# 업로드할 파일의 저장 경로 설정
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 업로드 폴더 생성
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

products = {}
users = {}


@app.route("/index")
def index():
    return render_template("indexSeller.html", logged_in=('id' in session), user=session.get('nickname'))

@app.route("/", methods=['GET', 'POST'])
def home():
    if 'id' in session:
        if session['role'] == 'seller':
            return render_template("homeSeller.html", logged_in=True, user=session.get('nickname'))
        return render_template("homeBuyer.html", logged_in=True, user=session.get('nickname'))
    return redirect(url_for("login_user"))  # 로그인하지 않은 경우 로그인 화면으로 리다이렉트


@app.route("/signUp", methods=['GET', 'POST'])
def sign_up():
    if request.method == "POST":
        id = request.form.get("id")
        password = request.form.get("password")
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        nickname = request.form.get("nickname")
        email = request.form.get("email")
        phone = request.form.get("phone")
        role = request.form.get("role")

        if DB.insert_user(id, password_hash, nickname, email, phone, role):
            return render_template("login.html")
        else:
            flash("user id already exists!")
            return render_template("signUp.html")

        # 사용자 정보를 딕셔너리에 저장
        # users[email] = {
        #     "id": id,
        #     "password": password,
        #     "nickname": nickname,
        #     "email": email,
        #     "phone": phone,
        #     "role": role
        # }
        #
        # if not DB.check_user_exists(email):
        #     users[email] = {
        #         "id": id,
        #         "password": password,
        #         "nickname": nickname,
        #         "email": email,
        #         "phone": phone,
        #         "role": role
        #     }
        #     DB.insert_user(id, email, password, nickname, phone, role)
        #     session['id'] = id
        #     return redirect(url_for("home"))
        # return render_template("signUp.html", error="이메일이 이미 등록되어 있습니다.")

        # 회원가입 후 세션에 저장하여 자동 로그인 처리
        session['id'] = id
        session['nickname'] = nickname
        session['role'] = role

        return redirect(url_for("home", logged_in=('id' in session), user=session.get('nickname')))

    return render_template('signUp.html', logged_in=False)

# 상품 상세 페이지
@app.route("/view_detail/<product_name>/")
def product_detail(product_name):
    try:
        logging.debug(f"Requested product name: {product_name}")
        all_products = DB.get_items()  # 리스트 반환
        logging.debug(f"All products: {all_products}")

        # 리스트에서 이름으로 상품 검색
        product = next((item for item in all_products if item and item.get("name") == product_name), None)

        if not product:
            logging.error(f"Product with name '{product_name}' not found.")
            return f"Product '{product_name}' not found", 404

        return render_template(
            "productDetailBuyer.html",
            product=product,
            logged_in=('id' in session),
            user=session.get('nickname')
        )
    except Exception as e:
        logging.error(f"Error retrieving product details: {e}")
        return f"An unexpected error occurred: {str(e)}", 500

@app.route("/review/<product_name>/")
def product_review_list(product_name):
    try:
        # Firebase에서 모든 리뷰 가져오기
        all_reviews = DB.get_reviews()  # DB.get_reviews()가 리스트를 반환한다고 가정
        if not all_reviews:
            return f"No reviews found for product '{product_name}'", 404

        # 리스트에서 None 값 제거
        valid_reviews = [review for review in all_reviews if review is not None]

        # 특정 상품의 리뷰만 필터링
        product_reviews = [
            review for review in valid_reviews
            if review.get("product_name") == product_name
        ]

        # 리뷰 정렬 (옵션: 리뷰 날짜 기준 최신순 정렬)
        product_reviews.sort(key=lambda x: x.get("review_date", ""), reverse=True)

        return render_template(
            "ProductreviewsBuyer.html",
            product_name=product_name,
            reviews=product_reviews,
            logged_in=('id' in session),
            user=session.get('nickname')
        )
    except Exception as e:
        logging.error(f"Error retrieving reviews for product '{product_name}': {e}")
        return f"An error occurred: {e}", 500




@app.route("/mypage")
def view_review():
    if session['role'] == 'seller':
        return render_template("mypageSell.html")
    elif session['role'] == 'buyer':
        return render_template("mypageBuy.html")
    else:
        return redirect(url_for("login"))

# 상품 리스트
@app.route("/browse", methods=["GET"])
def browse():
    try:
        # Firebase에서 데이터 가져오기
        all_products = DB.get_items()  # 리스트로 반환된 데이터
        logging.debug(f"DEBUG: All Products from Firebase: {all_products}")

        # 리스트 형식 확인 및 유효 데이터 필터링
        if isinstance(all_products, list):
            valid_products = [product for product in all_products if product is not None]
        else:
            # 예외 처리: 리스트가 아닌 경우 빈 리스트로 설정
            valid_products = []

        # 페이지네이션 처리
        page = request.args.get('page', default=1, type=int)
        items_per_page = 4
        total_products = len(valid_products)
        total_pages = (total_products + items_per_page - 1) // items_per_page

        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        products = valid_products[start_idx:end_idx]

        # 각 제품에 대한 기본 필드 설정
        for product in products:
            product["img_path"] = product.get("img_path", "default.jpg")

        return render_template(
            "browseBuyer.html",
            products=products,
            page=page,
            total_pages=total_pages
        )
    except Exception as e:
        logging.error(f"Error loading products: {e}")
        return f"Error loading products: {str(e)}", 500


# 상품 등록
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # 상품 등록 데이터 수집
        name = request.form.get("name")  # 상품 이름
        price = float(request.form.get("price").replace('₩', '').replace(',', ''))  # 판매 가격
        location = request.form.get("location")  # 직거래 지역
        condition = request.form.get("condition")  # 상태
        stock = int(request.form.get("stock"))  # 재고 수량
        description_short = request.form.get("description_short")  # 한 줄 소개
        description_long = request.form.get("description_long")  # 상세 설명
        category = request.form.get("category")  # 카테고리 선택
        ewha_green = request.form.get("ewha_green") == "on"  # 초록템 여부 (체크박스)

        # 이미지 처리 (대표 사진 1장만)
        image = request.files['file']
        image_filename = f"{name}_{image.filename}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)

        # Firebase에 저장할 데이터 구성
        product_data = {
            "name": name,
            "price": price,
            "location": location,
            "condition": condition,
            "stock": stock,
            "description_short": description_short,
            "description_long": description_long,
            "category": category,
            "ewha_green": ewha_green,
            "img_path": image_filename
        }

        # Firebase에 데이터 저장
        product_id = str(len(DB.get_items()) + 1)
        if DB.insert_item(product_id, product_data):
            return redirect(url_for("browse"))
        return render_template("error.html", message="상품 등록에 실패했습니다.")

    return render_template("register.html")


@app.route("/login", methods=['GET', 'POST'])
def login_user():
    if request.method == 'POST':
        # 로그인 처리
        id = request.form.get('id')
        password = request.form.get('password')
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

        user = DB.find_user(id, password_hash)

        if user:
            session['id'] = id
            session['nickname'] = user['nickname']  # 이 부분도 DB에서 가져온 사용자 닉네임으로 수정 필요
            session['role'] = user['role']
            print(f"Session data: {session}") # 세션 확인용 출력 
            return redirect(url_for("home"))
        else:
            flash("잘못된 ID or PW")
            return render_template("login.html", error="아이디 또는 비밀번호가 잘못되었습니다.", logged_in=False)

    # GET 요청 시 로그인 화면을 렌더링
    return render_template("login.html", logged_in=False)


@app.route("/findId", methods=['GET', 'POST'])
def find_id():
    if request.method == "POST":
        email = request.form.get("email")

        # 이메일로 아이디 찾기
        if email in users:
            id = users[email]["id"]
            return render_template("findId.html", id=id, found=True, logged_in=False)
        else:
            return render_template("findId.html", error="가입되지 않은 회원입니다.", logged_in=False)

    return render_template("findId.html", logged_in=False)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route('/review')
def reviews():
    reviews_data = [
        {"title": "리뷰 제목", "author": "작성자 닉네임", "date": "작성 날짜"},
        {"title": "리뷰 제목", "author": "작성자 닉네임", "date": "작성 날짜"},
        {"title": "리뷰 제목", "author": "작성자 닉네임", "date": "작성 날짜"},
    ]

    if session['role'] == 'seller':
        return render_template("productreviewsSeller.html", reviews=reviews_data, logged_in=('id' in session), user=session.get('nickname'))

    return render_template('productreviewsBuyer.html', reviews=reviews_data)

@app.route('/reviews', methods=['GET'])
def review_list():
    try:
        # Fetch and validate reviews
        reviews = DB.get_reviews()
        if isinstance(reviews, dict):
            reviews = list(reviews.values()) 
        valid_reviews = [review for review in reviews if review is not None]

        # Pagination logic
        page = request.args.get('page', default=1, type=int)
        reviews_per_page = 8
        total_reviews = len(valid_reviews)
        total_pages = (total_reviews + reviews_per_page - 1) // reviews_per_page

        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        start_idx = (page - 1) * reviews_per_page
        end_idx = start_idx + reviews_per_page
        paginated_reviews = valid_reviews[start_idx:end_idx]

        # Default handling for missing fields
        for review in paginated_reviews:
            review["img_path"] = review.get("img_path", "default.jpg")

        return render_template(
            "reviewList.html",
            reviews=paginated_reviews,
            page=page,
            total_pages=total_pages,
            logged_in=('id' in session),
            user=session.get('nickname')
        )
    except Exception as e:
        logging.error(f"Error loading reviews: {e}")
        return f"Error loading reviews: {str(e)}", 500

@app.route('/myreviews')
def myreview_list():
    try:
        reviews = DB.get_review_by_nickname(session.get('nickname'))
        if isinstance(reviews, dict):
            reviews = list(reviews.values()) 
        valid_reviews = [review for review in reviews if review is not None]
        
        # Pagination settings
        page = request.args.get('page', default=1, type=int)
        reviews_per_page = 8
        total_reviews = len(valid_reviews)
        total_pages = (total_reviews + reviews_per_page - 1) // reviews_per_page

        if page < 1:
            page = 1
        elif page > total_pages:
            page = total_pages

        start_idx = (page - 1) * reviews_per_page
        end_idx = start_idx + reviews_per_page
        paginated_reviews = valid_reviews[start_idx:end_idx]

        # Default handling for missing fields
        for review in paginated_reviews:
            review["img_path"] = review.get("img_path", "default.jpg")

        return render_template(
            "myreviewList.html",
            reviews=paginated_reviews,
            page=page,
            total_pages=total_pages,
            logged_in=('id' in session),
            user=session.get('nickname')
        )
    except Exception as e:
        logging.error(f"Error loading reviews: {e}")
        return f"Error loading reviews: {str(e)}", 500

@app.route("/reviews/register/<name>/")
def register_review_init(name):
    user_id = session.get('id')
    user_nickname = session.get('nickname')
    return render_template("reviewRegister.html", 
                           product_name=name, 
                           user_id=user_id, 
                           user_nickname=user_nickname,
                           user=user_nickname,
                           logged_in=('id' in session))

@app.route('/reviews/register', methods = ['GET', 'POST'])
def register_review():
    
    if request.method == "POST":
        review_title = request.form.get("review_title")
        review_content = request.form.get("review_content")
        rating = request.form.get("rating", type=int) 
        purchase_date = request.form.get("purchase_date")
        product_name = request.form.get("product_name")

        # 이미지 파일 처리
        image = request.files['image']
        image_filename = f"{product_name}_{image.filename}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_filename)
        image.save(image_path)


        # Firebase에 데이터 구성
        review_id = str(len(DB.get_reviews())+1)
        new_review = {
            "user_nickname": session.get('nickname'),
            "product_name":product_name,
            "review_title": review_title,
            "review_content": review_content, 
            "rating": rating,
            "img_path": image_filename,      
            "purchase_date": purchase_date,
            "review_date": datetime.today().strftime('%Y-%m-%d'),
            "review_id": review_id
        }

        # Firebase에 데이터 추가 
        DB.insert_review(review_id, new_review)
        return redirect(url_for("review_detail", review_id=review_id))
    return render_template("register_review.html")

@app.route('/reviews/<int:review_id>')
def review_detail(review_id):
    review = DB.get_review_by_id(review_id)
    if review:
        return render_template("reviewDetail.html", review=review,
                               logged_in=('id' in session),
                               user=session.get('nickname'))
    return "리뷰를 찾을 수 없습니다.", 404

@app.route('/show_heart/<name>/', methods=['GET'])
def show_heart(name):
    my_heart = DB.get_heart_byname(session['id'], name)
    return jsonify({'my_heart': my_heart})


@app.route('/like/<name>/', methods=['POST'])
def like(name):
    my_heart = DB.update_heart(session['id'], 'Y', name)
    return jsonify({'msg': '좋아요 완료!'})

@app.route('/unlike/<name>/', methods=['POST'])
def unlike(name):
   
    my_heart = DB.update_heart(session['id'], 'N', name)
    return jsonify({'msg': '좋아요 취소!'})




if __name__ == "__main__":
    app.run(debug=True)