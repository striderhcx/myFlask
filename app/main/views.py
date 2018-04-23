#coding=utf-8
from flask import render_template, redirect, url_for, abort, flash, request,\
    current_app, make_response # ,send_from_directory # [HCX]:temp unused(no preview)
from flask_login import login_required, current_user
from flask_sqlalchemy import get_debug_queries
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm,\
    CommentForm, AddPostCategoryForm, SendMessageForm
from .. import db, celery, mail, create_app
from ..tasks.celery_mail import send_async_email, send_async_webpush
from ..models import Permission, Role, User, Post, Comment, PostCategory, Star,\
    Message, Webpush
from ..decorators import admin_required, permission_required
import os
#from werkzeug.utils import secure_filename # [HCX]: temp unused!


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['FLASKY_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(
                'Slow query: %s\nParameters: %s\nDuration: %fs\nContext: %s\n'
                % (query.statement, query.parameters, query.duration,
                   query.context))
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'

#同步建立推送，不使用celery
def send_sync_webpush(username, postid):
    user = User.query.filter_by(username=username).first()
    print('user:', user)
    post = Post.query.get_or_404(postid)
    followers = user.followers
    print('followers:', user.followers)
    for follower in followers:
        print('follower:', follower)
        if follower.follower != user:
            print('follower.follower:', follower.follower)
            webpush = Webpush(sendto=follower.follower, author=user, post_id=post.id)
            db.session.add(webpush)
    db.session.commit()

@main.route('/about_me/', methods=['GET', 'POST'])
def about_me():
    return render_template('resume/dist/index.html')

@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data,
                    author=current_user._get_current_object(),
                    category=PostCategory.query.get(form.category.data))
        db.session.add(post)
        db.session.commit()
        #测试用celery发送邮件
        send_async_email.delay('2789508894@qq.com', "{}'s new post:".format(current_user.username), post.body)
        flash('celery email has send!')
        # send_async_webpush.delay(username=current_user.username,postid=post.id)
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
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts,
                           show_followed=show_followed, pagination=pagination,post_categories=PostCategory.query.all())


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    pagination = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('user.html', user=user, posts=posts,
                           pagination=pagination)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        # [HCX]: Add user upload avatar
        avatar = request.files['avatar']# [HCX]:the dict key name must the same as the form's avatar name!
        fname = avatar.filename
        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
        flag = '.' in fname and fname.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
        if not flag:
            flash('Upload file type is not support or is null!')
            return redirect(url_for('.user', username=current_user.username))
        avatar.save('{}{}_{}'.format(UPLOAD_FOLDER, current_user.username, fname))
        current_user.real_avatar = '/static/avatar/{}_{}'.format(current_user.username, fname)
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


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
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        # [HCX]: Add user upload avatar
        avatar = request.files['avatar']# [HCX]:the dict key name must the same as the form's avatar name!
        fname = avatar.filename
        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
        flag = '.' in fname and fname.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
        if not flag:
            flash('Upload file type is not support or is null!')
            return redirect(url_for('.user', username=user.username))
        avatar.save('{}{}_{}'.format(UPLOAD_FOLDER, user.username, fname))
        user.real_avatar = '/static/avatar/{}_{}'.format(user.username, fname)
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

@main.route('/post/new/', methods=['GET', 'POST'])
@login_required
def newpost():
    form = PostForm()
    if request.method == 'GET':
        return render_template('new_post.html', form=form)
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post = Post(title=form.title.data, body=form.body.data,
                    author=current_user._get_current_object(),
                    category=PostCategory.query.get(form.category.data))
        db.session.add(post)
        db.session.commit()
        send_sync_webpush(username=current_user.username, postid=post.id)
    return redirect(url_for('main.index'))


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // \
            current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                           comments=comments, pagination=pagination)


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

@main.route('/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    for comment in post.comments:
        db.session.delete(comment)
    db.session.delete(post)
    flash('The post has been delete!')
    return redirect(url_for('.user', username=post.author.username))

#路由捕获多个关键字参数:author_name和id
#展示用户名为author_username 的User对应的所有分类为id的文章
@main.route('/category_posts/<author_name>/<int:id>', methods=['GET', 'POST'])
@login_required
def category_posts(author_name, id):
    post_category = PostCategory.query.get_or_404(id)
    #找到作者
    post_author = User.query.filter_by(username=author_name).first()
    page = request.args.get('page', 1, type=int)
    #need to paginate: post_category.posts,只显示这篇被点击的该篇文章对应的作者的分类为id的文章
    pagination = post_category.posts.filter_by(author=post_author).order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    if len(posts):
        return render_template('show_category_posts.html', posts=posts, category=post_category,
                                pagination=pagination)
    else:
        #因为必须要保证posts大于0，才能保证不出错模板中posts[0]不出错，所以这里处理一下
        flash(u'暂无该分类文章')
        return render_template('show_category_posts.html', posts=posts, category=post_category)

#
@main.route('/add_post_category', methods=['GET', 'POST'])
@login_required
def add_post_category():
    form = AddPostCategoryForm()
    if form.validate_on_submit():
        new_category = PostCategory(name=form.new_category.data)
        db.session.add(new_category)
        #必须立即提交，否则不会马上看到生效的修改
        try:
            db.session.commit()
        except:
            flash(u'分类已存在!')
            #回滚，并且清空表单
            form.new_category.data=''
            db.session.rollback()
            return render_template('add_post_category.html', form=form)
        else:
            return redirect(url_for('.index'))
    return render_template('add_post_category.html', form=form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash('You are already following this user.')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash('You are not following this user.')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash('You are not following %s anymore.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of",
                           endpoint='.followers', pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by",
                           endpoint='.followed_by', pagination=pagination,
                           follows=follows)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('moderate.html', comments=comments,
                           pagination=pagination, page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    return redirect(url_for('.moderate',
                            page=request.args.get('page', 1, type=int)))

#添加收藏文章和取消收藏的路由2017-10-2
@main.route('/star/<int:id>')
@login_required
@permission_required(Permission.FOLLOW)
def star(id):
    post = Post.query.get_or_404(id)
    if current_user.staring(post):
        flash('You have already star the post!')
        return redirect(url_for('.post', id=post.id))
    current_user.star(post)
    flash('Star the post complete!')
    return redirect(url_for('.post',id=post.id))

@main.route('/unstar/<int:id>')
@login_required
@permission_required(Permission.FOLLOW)
def unstar(id):
    post=Post.query.get_or_404(id)
    if not current_user.staring(post):
        flash('You have not star the post.')
        return redirect(url_for('.post', id=post.id))
    current_user.unstar(post)
    flash('Cancel star complete!')
    return redirect(url_for('.post', id=post.id))

@main.route('/starposts/<username>')
def starposts(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    posts = user.starposts
    return render_template('starposts.html', user=user, title=u"收藏的文章", posts=posts)

###添加私信和推送消息的路由

@main.route('/<username>/showwebpush')
@login_required
@permission_required(Permission.COMMENT)
def showwebpush(username):
    page = request.args.get('page', 1, type=int)
    pagination = Webpush.query.order_by(Webpush.timestamp.desc()).filter_by(sendto=current_user).paginate(
            page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
            error_out=False)
    webpushs = pagination.items
    return render_template('user_showwebpush.html',webpushs=webpushs, pagination=pagination, page=page)

@main.route('/webpush/confirmed/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def webpush_confirmed(id):
    webpush = Webpush.query.get_or_404(id)
    webpush.confirmed = True
    db.session.add(webpush)
    return redirect(url_for('.showwebpush',page=request.args.get('page', 1, type=int),username=request.args.get('username')))

@main.route('/webpush/unconfirmed/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def webpush_unconfirmed(id):
    webpush = Webpush.query.get_or_404(id)
    webpush.confirmed = False
    db.session.add(webpush)
    return redirect(url_for('.showwebpush', page=request.args.get('page', 1, type=int), username=request.args.get('username')))

@main.route('/showwebpush/delete/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def webpush_delete(id):
    webpush = Webpush.query.get_or_404(id)
    db.session.delete(webpush)
    flash('webpush delete success')
    return redirect(url_for('.showwebpush', page=request.args.get('page', 1, type=int), username=request.args.get('username')))

#发送私信
@main.route('/sendmessage/<username>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.COMMENT)
def sendmessage(username):
    user = User.query.filter_by(username=username).first()
    form = SendMessageForm()
    if form.validate_on_submit():
        message = Message(body=form.body.data, \
                    author=current_user._get_current_object(),
                    sendto=user)
        db.session.add(message)
        db.session.commit()
        flash('message send ok!')
        return redirect(url_for('.user', username=username))
    return render_template('sendmessage.html', form=form)

#查看自己的私信
@main.route('/showmessage')
@login_required
@permission_required(Permission.COMMENT)
def showmessage():
    page = request.args.get('page', 1, type=int)
    pagination = Message.query.order_by(Message.timestamp.desc()).filter_by(sendto=current_user).paginate(
        page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
        error_out=False)
    messages = pagination.items
    return render_template('showmessage.html', messages=messages,
                            pagination=pagination, page=page)
#标记私信为已读
@main.route('/message/confirmed/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def message_confirmed(id):
    message = Message.query.get_or_404(id)
    message.confirmed = True
    db.session.add(message)
    return redirect(url_for('.showmessage', page=request.args.get('page', 1 ,type=int)))

#标记私信为未读
@main.route('/message/unconfirmed/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def message_unconfirmed(id):
    message = Message.query.get_or_404(id)
    message.confirmed = False
    db.session.add(message)
    return redirect(url_for('.showmessage', page=request.args.get('page', 1 ,type=int)))

#删除私信
@main.route('/showmessage/delete/<int:id>')
@login_required
@permission_required(Permission.COMMENT)
def message_delete(id):
    message = Message.query.get_or_404(id)
    db.session.delete(message)
    flash('delete message success!')
    return redirect(url_for('.showmessage', page=request.args.get('page', 1 ,type=int)))
