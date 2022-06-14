#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import dateutil.parser
import babel
from flask import (
  Flask,
  render_template,
  request,
  Response,
  flash,
  redirect,
  url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from forms import *
from flask_migrate import Migrate
import sys

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(10))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(10))
    genres = db.Column(db.ARRAY(db.String), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)


class Show(db.Model):
  __tablename__ = 'show'

  id = db.Column(db.Integer, primary_key=True)
  artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
  venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
  start_time = db.Column(db.DateTime, nullable=False)


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data=[{
    "city": "San Francisco",
    "state": "CA",
    "venues": [{
      "id": 1,
      "name": "The Musical Hop",
      "num_upcoming_shows": 0,
    }, {
      "id": 3,
      "name": "Park Square Live Music & Coffee",
      "num_upcoming_shows": 1,
    }]
  }, {
    "city": "New York",
    "state": "NY",
    "venues": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }]

  query_select = db.session.query(Venue.city).distinct().all()

  for city in query_select:
    print(f'city: {city[0]}', file=sys.stdout)
    result_city = city[0]
    venues = Venue.query.filter_by(city=f'{result_city}').all()
    venues = Venue.query.filter_by(city=f'{result_city}').filter().all()
    print(f'city: {venues}', file=sys.stdout)
    city_venues = {}
    venues_list = []
    for venue in venues:
      print(f'venue: {venue.id}', file=sys.stdout)
      city_venues['state'] = venue.state
      num_of_shows = Show.query.filter_by(
        venue_id=venue.id
        ).filter(
          Show.start_time>datetime.now()
          ).count()

      print(f'shows: {num_of_shows}', file=sys.stdout)
      venue_dict = {
        'id':venue.id,
        'name':venue.name,
        'num_upcoming_shows':num_of_shows
      }
      venues_list.append(venue_dict)
      city_venues['city'] = result_city
      city_venues['venues'] = venues_list
    print(f'venues list: {city_venues}', file=sys.stdout)
    db_data = [city_venues]
  
  return render_template('pages/venues.html', areas=db_data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  term = request.form.get('search_term', '')

  query = Venue.query.filter(Venue.name.ilike(f'%{term}%'))
  db_response = {'count':query.count(), 'data':query.all()}
  return render_template('pages/search_venues.html', results=db_response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  date_now = datetime.now()
  query_filter = db.session.query(
      Venue, Show, Artist
    ).filter(
      Venue.id == Show.venue_id
    ).filter(
      Show.artist_id == Artist.id
    ).filter(
      Venue.id == venue_id
    ).all()
          
  venue: Venue = query_filter[0][0]
  
  db_data = {
    'id':venue.id,
    'name':venue.name, 
    'genres':venue.genres,
    'address':venue.address,
    'city':venue.city, 
    'state':venue.state,
    'phone':venue.phone,
    'website':venue.website_link,
    'facebook_link':venue.facebook_link, 
    'seeking_talent':venue.seeking_talent,
    'image_link':venue.image_link,   
    'past_shows':[],
    'upcoming_shows':[],
    'past_shows_count':0,
    'upcoming_shows_count':0
    }
  upcoming_shows_list = []
  past_shows_list = []
  for relation in query_filter:
    show: Show = relation[1]
    artist: Artist = relation[2]
    
    if show.start_time > date_now:
      upcoming_show = {
        'artist_id':artist.id,
        'artist_name':artist.name,
        'artist_image_link':artist.image_link,
        'start_time':show.start_time.strftime("%Y/%m/%d, %H:%M:%S")
        }
      upcoming_shows_list.append(upcoming_show)
    else:
      past_show = {
        'artist_id':artist.id,
        'artist_name':artist.name,
        'artist_image_link':artist.image_link,
        'start_time':show.start_time.strftime("%Y/%m/%d, %H:%M:%S")
        }
      past_shows_list.append(past_show)

  db_data["upcoming_shows"] = upcoming_shows_list
  db_data["past_shows"] = past_shows_list
  db_data["past_shows_count"] = len(past_shows_list)
  db_data["upcoming_shows_count"] = len(upcoming_shows_list)

  return render_template('pages/show_venue.html', venue=db_data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form)

  try:
    if request.method == 'POST' and form.validate():
      venue = Venue(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        address=form.address.data,
        phone=form.phone.data,
        image_link=form.image_link.data,
        genres=form.genres.data,
        facebook_link=form.facebook_link.data,
        website_link=form.website_link.data,
        seeking_talent=form.seeking_talent.data,
        seeking_description=form.seeking_description.data
      )
      db.session.add(venue)
      db.session.commit()
      flash(f'Venue {venue.name} was successfully listed!')
    else:
      flash('An error occurred. Venue could not be listed')
    
  except Exception as e:
    db.session.rollback()
    flash(f'An error occurred. Venue {form.name.data} could not be listed')
    raise e
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  db_data = Artist.query.with_entities(Artist.id, Artist.name)
  return render_template('pages/artists.html', artists=db_data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term=request.form.get('search_term', '')
  query = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
  db_response = {'count':query.count(), 'data':query.all()}
  return render_template('pages/search_artists.html', results=db_response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  date_now = datetime.now()
  query_filter = db.session.query(
    Artist, Show, Venue
    ).filter(
      Artist.id == Show.artist_id
    ).filter(
      Show.venue_id == Venue.id
    ).filter(
      Artist.id == artist_id
    ).all()
          
  artist: Artist = query_filter[0][0]
  
  db_data = {
    'id':artist.id,
    'name':artist.name, 
    'genres':artist.genres,
    'city':artist.city, 
    'state':artist.state, 
    'phone':artist.phone, 
    'seeking_venue':artist.seeking_venue,
    'image_link':artist.image_link,
    'website_link':artist.website_link,
    'facebook_link':artist.facebook_link,
    'past_shows':[],
    'upcoming_shows':[],
    'past_shows_count':0,
    'upcoming_shows_count':0
    }
  upcoming_shows_list = []
  past_shows_list = []
  for relation in query_filter:
    show: Show = relation[1]
    venue: Venue = relation[2]
    
    if show.start_time > date_now:
      upcoming_show = {
        'venue_id':venue.id,
        'venue_name':venue.name,
        'venue_image_link':venue.image_link,
        'start_time':show.start_time.strftime("%Y/%m/%d, %H:%M:%S")
        }
      upcoming_shows_list.append(upcoming_show)
    else:
      past_show = {
        'venue_id':venue.id,
        'venue_name':venue.name,
        'venue_image_link':venue.image_link,
        'start_time':show.start_time.strftime("%Y/%m/%d, %H:%M:%S")
      }
      past_shows_list.append(past_show)

  db_data["upcoming_shows"] = upcoming_shows_list
  db_data["past_shows"] = past_shows_list
  db_data["past_shows_count"] = len(past_shows_list)
  db_data["upcoming_shows_count"] = len(upcoming_shows_list)

  return render_template('pages/show_artist.html', artist=db_data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  db_artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=db_artist)
  
  return render_template('forms/edit_artist.html', form=form, artist=db_artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)

  try:
    if request.method == 'POST' and form.validate():
      artist = Artist.query.filter_by(id=artist_id).first()
      artist.name = form.name.data
      artist.city = form.city.data
      artist.state = form.state.data
      artist.genres = form.genres.data
      if form.phone.data != None: artist.phone = form.phone.data 
      if form.facebook_link.data != None: artist.facebook_link = form.facebook_link.data 
      if form.website_link.data != None: artist.website_link = form.website_link.data 
      if form.image_link.data != None: artist.image_link = form.image_link.data 
      if form.seeking_description.data != None: artist.seeking_description = form.seeking_description.data 
      if form.seeking_venue.data != None: artist.seeking_venue = form.seeking_venue.data
      db.session.commit()

  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  db_venue = Venue.query.get(venue_id)
  form = VenueForm(obj=db_venue)

  return render_template('forms/edit_venue.html', form=form, venue=db_venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

  form = VenueForm(request.form)

  try:
    if request.method == 'POST' and form.validate():
      venue = Venue.query.filter_by(id=venue_id).first()
      venue.name = form.name.data
      venue.city = form.city.data
      venue.state = form.state.data
      venue.genres = form.genres.data 
      if form.phone.data != None: venue.phone = form.phone.data 
      if form.facebook_link.data != None: venue.facebook_link = form.facebook_link.data 
      if form.website_link.data != None: venue.website_link = form.website_link.data 
      if form.image_link.data != None: venue.image_link = form.image_link.data 
      if form.seeking_description.data != None: venue.seeking_description = form.seeking_description.data
      if form.seeking_talent.data != None: venue.seeking_talent = form.seeking_talent.data

      db.session.commit()

  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)

  try:
    if request.method == 'POST' and form.validate():
      artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        image_link=form.image_link.data,
        genres=form.genres.data,
        facebook_link=form.facebook_link.data,
        website_link=form.website_link.data,
        seeking_venue=form.seeking_venue.data,
        seeking_description=form.seeking_description.data
      )
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    else:
      flash('Please fill all the required details')
  except:
    db.session.rollback()
    flash(f'An error occurred. Artist {form.name.data} could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  query_filter = db.session.query(
    Show, Venue, Artist
  ).filter(
    Show.venue_id == Venue.id
  ).filter(
    Artist.id == Show.artist_id
  ).order_by(
    Venue.id
  ).all()
  db_data = []
  for relation in query_filter:
    show = relation[0]
    venue = relation[1]
    artist = relation[2]
    show_data = {}
    show_data['venue_id'] = venue.id
    show_data['venue_name'] = venue.name
    show_data['artist_id'] = artist.id
    show_data['artist_name'] = artist.name
    show_data['artist_image_link'] = artist.image_link
    show_data['start_time'] = show.start_time.strftime("%Y/%m/%d, %H:%M:%S")
    db_data.append(show_data)
    
  return render_template('pages/shows.html', shows=db_data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)

  try:
    if request.method == 'POST' and form.validate():
      show = Show(
        artist_id=form.artist_id.data,
        venue_id=form.venue_id.data,
        start_time=form.start_time.data
      )
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed')
    else:
      flash('Please fill in all the required fields')
  except:
    db.session.rollback()
    flash('An error occurred. Show could not be listed')
  finally:
    db.session.close()

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
