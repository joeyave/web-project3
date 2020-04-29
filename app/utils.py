import datetime
import decimal


def h1_left_align(soup):
    for tag in soup.find_all("h1"):
        tag['style'] = "text-align: left;"


def responsive_images(soup):
    for tag in soup.find_all("img"):
        tag['style'] = """
        max-width: 100%; height: auto;
        padding: 1rem;
        """


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def alchemyencoder(obj):
    """JSON encoder function for SQLAlchemy special classes."""
    if isinstance(obj, datetime.date):
        return obj.strftime('%I:%M%p %d-%m-%Y')
    elif isinstance(obj, decimal.Decimal):
        return float(obj)
