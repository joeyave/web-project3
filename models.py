from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    timestamp = db.Column(db.DateTime(), index=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    replies = db.relationship(
        'Comment', backref=db.backref('parent', remote_side=[id]),
        lazy='dynamic')

    def add_reply(self, text):
        return Comment(text=text, parent=self)
