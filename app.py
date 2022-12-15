import cv2 as cv
import pytesseract as tes
import os
from flask import Flask, flash, render_template, request, send_file, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename

from os.path import join, dirname, realpath

from tos3 import get_unique_filename, upload_file_to_s3

from sqlite3 import connect
from contextlib import closing

DATABASEURL = 'file:runawayads.db?mode=rw'

UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def index():
    return render_template('home.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=['GET', 'POST'])
def image_to_text():
    filename = ""
    if request.method == 'POST':
        the_id = 0
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img = cv.imread(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_text_guess = tes.image_to_string(img)

            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
                f.filename = get_unique_filename(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                print(f.filename)
                image_url = upload_file_to_s3(f)
                print(image_url["url"])

                try:
                    with connect(DATABASEURL, isolation_level=None, uri=True) as conn:
                        with closing(conn.cursor()) as cursor:
                            cursor.execute("INSERT into ad_images (url, rough) VALUES(:url, :rough)",
                            {'url': image_url["url"],
                            'rough': str(image_text_guess)})
                            the_id = cursor.lastrowid
                except Exception as e:
                    return {"msg": str(e)}, 401

            print(the_id)
            return redirect(url_for('collection', id = the_id))
    return render_template("upload.html")

@app.route('/collection/<id>', methods=['GET', 'POST'])
def collection(id):
    if request.method == 'GET':
        try:
            with connect(DATABASEURL, isolation_level=None, uri=True) as conn:
                with closing(conn.cursor()) as cursor:
                    smt = cursor.execute("SELECT * FROM ad_images WHERE image_id = :image_id", {"image_id": id})
                    data = smt.fetchone()
                    print(data)
        except Exception as e:
            return {"msg": str(e)}, 401
        return render_template("collection.html", url = data[1], raw_text = data[2], id = id)
    else:
        text = request.form.get("freeform")
        try:
            with connect(DATABASEURL, isolation_level=None, uri=True) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("INSERT into ads (transcript, image_id) VALUES(:transcript, :image_id)",
                    {'transcript': text,
                    'image_id': id})
                    the_id = cursor.lastrowid
        except Exception as e:
            return {"msg": str(e)}, 401
        return redirect(url_for('information', id = the_id))

        
@app.route("/information/<id>", methods=['GET', 'POST'])
def information(id):
    if request.method == 'GET':
        newspapers = ["Mercury", "Cornwall Chronicles", "Royal Gazette"]

        try:
            with connect(DATABASEURL, isolation_level=None, uri=True) as conn:
                with closing(conn.cursor()) as cursor:
                    smt = cursor.execute("SELECT transcript, image_id FROM ads WHERE ad_id = :ad_id", {"ad_id": id})
                    data = smt.fetchone()
                    print(data)
        except Exception as e:
            return {"msg": str(e)}, 401
        
        try:
            with connect(DATABASEURL, isolation_level=None, uri=True) as conn:
                with closing(conn.cursor()) as cursor:
                    smt = cursor.execute("SELECT url FROM ad_images WHERE image_id = :image_id", {"image_id": data[1]})
                    image_data = smt.fetchone()
                    print(image_data)
        except Exception as e:
            return {"msg": str(e)}, 401

        return render_template('form.html', text=data[0], filename=image_data[0], newspapers=newspapers, id=id)

    if request.method == 'POST':
        #newspaper info
        newspaper = request.form.get("newspaper")
        month = request.form.get("month")
        day = request.form.get("day")
        year = request.form.get("year")

        formatted_dated = None
        if month and day and year:
            formatted_dated = f"{month}/{day}/{year}"

        #enslaver info
        poster = request.form.get("poster")
        enslaver = request.form.get("enslaver")
        location = request.form.get("location")
        comments_poster = request.form.get("comments_poster")

        #runaway info
        name = request.form.get("name")
        other_name = request.form.get("other_name")
        reward = request.form.get("reward")
        race = request.form.get("race")
        ethnicity = request.form.get("ethnicity")

        clothing = request.form.get("clothing")
        personality = request.form.get("personality")

        gender = request.form.get("gender")
        

        literacy = request.form.get("literacy")
        language = request.form.get("language")
    
        methodofescape = request.form.get("methodofescape")
        escapelocation = request.form.get("escapelocation")
       
        physical = request.form.get("physical")
        other_comment = request.form.get("other_comment")
        brand = request.form.get("radio")


        try:
            with connect(DATABASEURL, isolation_level=None, uri=True) as conn:
                with closing(conn.cursor()) as cursor:
                    cursor.execute("UPDATE ads SET newspaper = :newspaper, date = :date WHERE ad_id = :ad_id;", {"newspaper": newspaper, "date": formatted_dated, "ad_id": id})

                    cursor.execute("INSERT into poster (enslaver_name, poster_name, location, comments, ad_id) VALUES(:enslaver, :poster, :location, :comments, :id)",
                    {'enslaver': enslaver,
                    'poster': poster, 
                    'location': location, 
                    'comments': comments_poster,
                    'id': id})

                    cursor.execute("""INSERT into runaways 
                    (ad_id, method_escape, place_escape, name, other_name, personality, racial_category, ethnicity, literacy, speech, bodily_description, clothing, gender, branding, reward, comments) 
                    VALUES(:ad_id, :method_escape, :place_escape, :name, :other_name, :personality, :racial_category, :ethnicity, :literacy, :speech, :bodily_description, :clothing, :gender, :branding, :reward, :comments)""",
                    {'ad_id': id,
                    'method_escape': methodofescape, 
                    'place_escape': escapelocation, 
                    'name': name,
                    'other_name': other_name,
                    'personality': personality,
                    'racial_category': race,
                    'ethnicity': ethnicity,
                    'literacy': literacy,
                    'speech': language,
                    'bodily_description':physical, 
                    'clothing':clothing,
                    'gender':gender,
                    'branding':brand, 
                    'reward':reward,
                    'comments': other_comment})

        except Exception as e:
            return {"msg": str(e)}, 401



        return redirect("/")
    return render_template('form.html')

@app.route('/memorial', methods=['GET'])
def all_name():
    try:
        with connect(DATABASEURL, isolation_level=None, uri=True) as conn:
            with closing(conn.cursor()) as cursor:
                smt = cursor.execute("SELECT name, other_name FROM runaways;")
                names = smt.fetchall()
    except Exception as e:
        return {"msg": str(e)}, 401
    
    formatted_names = []
    for name in names:
        if not name[0]:
            formatted_names.append("unknown")
        else:
            if not name[1]:
                formatted_names.append(name[0])
            else:
                the_name = name[0] + " who also goes by " + name[1]
                formatted_names.append(the_name)
            
    return render_template('memorial.html', names=formatted_names)


        

if __name__ == '__main__':
    app.run(host='localhost', port=9801)