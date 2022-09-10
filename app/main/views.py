from flask import (
    render_template,
    flash, redirect,
    url_for,
    abort,
    current_app,
    request,
    make_response
)

from . import main
from .. import db
from ..models import Permission, User, Post, Comment
from flask_login import login_required, current_user
from .forms import EditProfileAdminForm, EditProfileForm, PostForm, CommentForm
from ..decorators import admin_required, permission_required
from flask_sqlalchemy import get_debug_queries

# Index endpoint
@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('.index'))

    page = request.args.get('page', 1, type=int)
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))

    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query

    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['APP_POSTS_PER_PAGE'],
        error_out=False
    )

    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination, show_followed=show_followed)


# User endpoint
@main.get('/user/<string:username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    if user is None:
        abort(404)

    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        flash('Your profile has been updated')
        return redirect(url_for('.user', username=current_user.username))

    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('editProfile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        db.session.commit()
        flash('Profile has been updated')
        return redirect(url_for('.user', username=user.username))

    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('editProfile.html', form=form, user=user)


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            body=form.body.data,
            post=post,
            author=current_user._get_current_object()
        )

        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published')
        return redirect(url_for('.post', id=post.id, page=-1))

    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['APP_COMMENTS_PER_PAGE'] + 1

    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['APP_COMMENTS_PER_PAGE'],
        error_out=False
    )

    comments = pagination.items
    return render_template('post.html', posts=[post], form=form, comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and not current_user.can(Permission.ADMIN):
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('Your post has been updated !')
        return redirect(url_for('.post', id=post.id))

    form.body.data = post.body
    return render_template('editPost.html', form=form)


@main.get('/follow/<string:username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))

    if current_user.is_following(user):
        flash('You are already following this user')
        return redirect(url_for('.user', username=username))

    current_user.follow(user)
    db.session.commit()
    flash(f'You start following the user: {username}')
    return redirect(url_for('.user', username=username))


@main.get('/unfollow/<string:username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))

    if not current_user.is_following(user):
        flash('You are not following this user')
        return redirect(url_for('.user', username=username))

    current_user.unfollow(user)
    db.session.commit()
    flash(f'You have stopped following the user: {username}')
    return redirect(url_for('.user', username=username))


@main.get('/followers/<string:username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect('.index')

    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['APP_FOLLOWERS_PER_PAGE'],
        error_out=False
    )

    follows = [{ 'user': item.follower, 'timestamp': item.timestamp } for item in pagination.items]
    return render_template('followers.html', user=user, title='Followers of the user', endpoint='.followers',
        pagination=pagination, follows=follows)


@main.get('/followed_by/<string:username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user')
        return redirect('.index')

    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['APP_FOLLOWERS_PER_PAGE'],
        error_out=False
    )

    follows = [{ 'user': item.followed, 'timestamp': item.timestamp } for item in pagination.items]
    return render_template('followers.html', user=user, title='Followed by', endpoint='.followed_by',
        pagination=pagination, follows=follows)


@main.get('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*25*60*60)
    return resp


@main.get('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.get('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['APP_COMMENTS_PER_PAGE'],
        error_out=False
    )

    comments = pagination.items
    return render_template('moderate.html', comments=comments, pagination=pagination, page=page)


@main.get('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.get('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['APP_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                f'Slow query: {query.statement}\nParameters: {query.parameters}\nTime: {query.duration}\nContext: {query.context}'
            )

    return response
