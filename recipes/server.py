import os
import sys
import tempfile

import boto3
from botocore.client import Config

from PIL import Image, ImageOps

from flask import Flask, render_template, request, jsonify
from flask.ext import restless

from sqlalchemy import create_engine, Column, Integer, Text, ForeignKey, String, Boolean, Table
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# FLASK SETUP

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(ROOT_DIR, 'static')

app = Flask(__name__)

# DEFAULT CONFIGURATION

app.config['DEBUG'] = True
app.config['SERVER_HOST'] = '0.0.0.0'
app.config['SERVER_PORT'] = 5000
app.config['DATABASE'] = 'sqlite:///recipes.db'
app.config['LANGUAGE'] = 'en'
try:
    app.config.from_object('settings')
except ImportError:
    pass

if app.config['DEBUG']:
    from werkzeug import SharedDataMiddleware
    app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
        '/static/': STATIC_DIR,
    })

# AWS SETUP

AWS_CONFIG = Config(
    signature_version='s3v4',
    region_name=app.config['AWS_REGION'],
)

# SQLALCHEMY TABLES

engine = create_engine(app.config['DATABASE'], convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()

recipe_garniture = Table('recipe_garniture', Base.metadata,
    Column('recipe_id', Integer, ForeignKey('recipe.id')),
    Column('garniture_id', Integer, ForeignKey('recipe.id'))
)

class Recipe(Base):
    __tablename__ = 'recipe'
    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True)
    image = Column(String(200))
    image_orientation = Column(String(20))

    persons = Column(Integer)
    recipe = Column(Text)
    garniture = Column(Text)

    favorite = Column(Boolean)
    has_tried = Column(Boolean)

    garnitures = relationship("Recipe", backref='as_garniture',
                              secondary=recipe_garniture,
                              primaryjoin=id == recipe_garniture.c.recipe_id,
                              secondaryjoin=id == recipe_garniture.c.garniture_id,
                              lazy='dynamic')

    def __repr__(self):
        return "<Recipe: {0}>".format(self.name)

class Timing(Base):
    __tablename__ = 'timing'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    recipe = relationship("Recipe", backref='timings', lazy='dynamic')
    description = Column(String(200))
    minutes = Column(Integer)

class Ingredient(Base):
    __tablename__ = 'ingredient'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    recipe = relationship("Recipe", backref='ingredients', lazy='dynamic')
    name = Column(String(100))
    amount  = Column(String(100))

class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipe.id'))
    recipe = relationship("Recipe", backref='tags', lazy='dynamic')
    name = Column(String(100))

# ReST API

# Create the Flask-Restless API manager.
manager = restless.APIManager(app, session=db_session, flask_sqlalchemy_db=Base)

# Create API endpoints, which will be available at /api/<tablename> by
# default. Allowed HTTP methods can be specified as well.
manager.create_api(Recipe,
                   methods=['GET', 'POST', 'DELETE', 'PATCH'],
                   exclude_columns=['tags.recipe_id', 'tags.id', 'ingredients.recipe_id', 'ingredients.id', 'timings.recipe_id', 'timings.id', 'garnitures'],
                   results_per_page=0)

@app.route('/api/garniture/<int:id>', methods=['POST', 'GET'])
def api_garnitures(id):
    recipe = Recipe.query.filter_by(id=id).first()
    if request.method == 'POST':
        recipe.garnitures = Recipe.query.filter(Recipe.id.in_(request.json['ids']))
        db_session.add(recipe)
        db_session.commit()
    garnitures = [{'name': g.name, 'id': g.id} for g in recipe.garnitures]
    return jsonify(objects=garnitures)

@app.route('/api/as-garniture/<int:id>')
def api_as_garniture(id):
    recipe = Recipe.query.filter_by(id=id).first()
    garnitures = [{'name': g.name, 'id': g.id} for g in recipe.as_garniture]
    return jsonify(objects=garnitures)

@app.route('/api/ingredient/')
def api_ingredients():
    ingredients = list(n[0] for n in db_session.query(Ingredient.name).filter(Ingredient.name.like('%%%s%%' % request.args.get('term', ''))).order_by(Ingredient.name).distinct())
    return jsonify(objects=ingredients)

@app.route('/api/timing/')
def api_timing():
    timings = list(n[0] for n in db_session.query(Timing.description).filter(Timing.description.like('%%%s%%' % request.args.get('term', ''))).order_by(Timing.description).distinct())
    return jsonify(objects=timings)

@app.route('/api/tag/')
def api_tag():
    tags = list(n[0] for n in db_session.query(Tag.name).filter(Tag.name.like('%%%s%%' % request.args.get('term', ''))).order_by(Tag.name).distinct())
    return jsonify(objects=tags)

@app.route('/api/garniture-recipes/')
def api_garniture_recipes():
    tags = list({'label': n[1], 'value': n[0]} for n in db_session.query(Recipe.id, Recipe.name).filter(Recipe.name.like('%%%s%%' % request.args.get('term', ''))).order_by(Recipe.name).distinct())
    return jsonify(objects=tags)

def _resize_image(img):
    if img.size[1] / (img.size[0] / (img.size[1] / 420.0)) < 240:
        height = 240
        width = int(img.size[0] / (img.size[1] / 240.0))
    else:
        width = 420
        height = int(img.size[1] / (img.size[0] / 420.0))

    return ImageOps.fit(img, (width, height), Image.ANTIALIAS)

@app.route('/api/set-image/', methods=['POST'])
def api_set_image():
    recipe = Recipe.query.filter_by(id=request.form['id']).first()

    f = request.files['image']
    tmp = tempfile.NamedTemporaryFile()
    f.save(tmp.name)

    img = Image.open(tmp.name)
    scale = float(img.size[0]) / float(img.size[1])
    is_horizontal = scale > 1

    img = _resize_image(img)

    img.save(tmp.name, 'png')

    s3 = boto3.client(
        's3',
        aws_access_key_id=app.config['AWS_ACCESS_KEY'],
        aws_secret_access_key=app.config['AWS_SECRET_KEY'],
        config=AWS_CONFIG,
    )
    filename = 'recipe-%s%s' % (recipe.id, os.path.splitext(f.filename)[-1])
    s3.upload_file(tmp.name, app.config['AWS_BUCKET'], filename)

    recipe.image = filename
    recipe.image_orientation = 'horizontal' if is_horizontal else 'vertical'
    db_session.add(recipe)
    db_session.commit()
    return jsonify({})

@app.route('/api/image-preview/', methods=['POST'])
def api_image_preview():
    import base64
    from cStringIO import StringIO

    raw = StringIO()
    request.files['image'].save(raw)
    raw.seek(0)

    img = Image.open(raw)
    img = _resize_image(img)

    out = StringIO()
    img.save(out, 'png')

    return jsonify(image=base64.b64encode(out.getvalue()))

@app.route('/')
def index():
    return render_template(
        'index.html',
        language=app.config['LANGUAGE'],
        aws_root=app.config['AWS_ROOT'],
    )

if __name__ == '__main__':

    def print_help():
        print """Recipe Database Management

usage: %s [-h] <command>

commands:
  runserver  run the development server
  initdb     create the database and tables
""" % sys.argv[0]

    if len(sys.argv) == 1:
        print_help()
    elif sys.argv[1] == 'runserver':
        app.debug = app.config['DEBUG']
        app.run(host=app.config['SERVER_HOST'], port=app.config['SERVER_PORT'])
    elif sys.argv[1] == 'initdb':
        Base.metadata.create_all(bind=engine)
    else:
        print_help()
