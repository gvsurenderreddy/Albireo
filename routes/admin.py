# -*- coding: utf-8 -*-
from flask import request, Blueprint
from utils.http import json_resp
import httplib2
import json
from service.admin import admin_service
from service.auth import auth_user
from flask_login import login_required
from domain.User import User


admin_api = Blueprint('bangumi', __name__)

@admin_api.route('/bangumi', methods=['POST', 'GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def collection():
    if request.method == 'POST':
        try:
            content = request.get_data(True, as_text=True)
            return admin_service.add_bangumi(content)
        except Exception as exception:
            raise exception
            # resp = make_response(jsonify({'msg': 'error'}), 500)
            # resp.headers['Content-Type'] = 'application/json'
            # return resp
    else:
        page = int(request.args.get('page', 1))
        count = int(request.args.get('count', 10))
        sort_field = request.args.get('order_by', 'update_time')
        sort_order = request.args.get('sort', 'desc')
        name = request.args.get('name', None)
        return admin_service.list_bangumi(page, count, sort_field, sort_order, name)


@admin_api.route('/bangumi/<id>', methods=['PUT', 'GET', 'DELETE'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def one(id):
    if request.method == 'PUT':
        return admin_service.update_bangumi(id, json.loads(request.get_data(True, as_text=True)))
    elif request.method == 'GET':
        return admin_service.get_bangumi(id)
    else:
        return admin_service.delete_bangumi(id)

@admin_api.route('/query', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def search_bangumi():
    bangumi_tv_url_base = 'http://api.bgm.tv/search/subject/'
    bangumi_tv_url_param = '?responseGroup=simple&max_result=10&start=0'
    name = request.args.get('name', None)
    result = {"data": []}
    if name is not None and len(name) > 0:
        bangumi_tv_url = bangumi_tv_url_base + name + bangumi_tv_url_param
        h = httplib2.Http('.cache')
        (resp, content) = h.request(bangumi_tv_url, 'GET')
        if resp.status == 200:
            try:
                bgm_content = json.loads(content)
            except ValueError as e:
                return json_resp(result)
            list = [bgm for bgm in bgm_content['list'] if bgm['type'] == 2]
            if len(list) == 0:
                return json_resp(result)

            bgm_id_list = [bgm['id'] for bgm in list]
            bangumi_list = admin_service.get_bangumi_from_bgm_id_list(bgm_id_list)

            for bgm in list:
                bgm['bgm_id'] = bgm['id']
                bgm['id'] = None
                # if bgm_id has found in database, give the database id to bgm.id
                # that's we know that this bangumi exists in our database
                for bangumi in bangumi_list:
                    if bgm['bgm_id'] == bangumi.bgm_id:
                        bgm['id'] = bangumi.id
                        break
                bgm['image'] = bgm['images']['large']
                # remove useless keys
                bgm.pop('images', None)
                bgm.pop('collection', None)
                bgm.pop('url', None)
                bgm.pop('type', None)

            result['data'] = list
        elif resp.status == 502:
            # when bangumi.tv is down
            result['msg'] = 'bangumi is down'

    return json_resp(result)

@admin_api.route('/query/<bgm_id>', methods=['GET'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def query_one_bangumi(bgm_id):
    bangumi_tv_url_base = 'http://api.bgm.tv/subject/'
    bangumi_tv_url_param = '?responseGroup=large'
    if bgm_id is not None:
        bangumi_tv_url = bangumi_tv_url_base + bgm_id + bangumi_tv_url_param
        h = httplib2.Http('.cache')
        (resp, content) = h.request(bangumi_tv_url, 'GET')
        return content
    else:
        return json_resp({})


@admin_api.route('/episode')
@login_required
@auth_user(User.LEVEL_ADMIN)
def episode_list():
    if request.method == 'GET':
        page = int(request.args.get('page', 1))
        count = int(request.args.get('count', 10))
        sort_field = request.args.get('order_by', 'bangumi_id')
        sort_order = request.args.get('sort', 'desc')
        status = request.args.get('status', None)
        return admin_service.list_episode(page, count, sort_field, sort_order, status)


@admin_api.route('/episode/<episode_id>/thumbnail', methods=['PUT'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def episode_thumbnail(episode_id):
    content = json.loads(request.get_data(True, as_text=True))
    return admin_service.update_thumbnail(episode_id, content['time'])


@admin_api.route('/episode/<episode_id>', methods=['GET', 'PUT'])
@login_required
@auth_user(User.LEVEL_ADMIN)
def episode(episode_id):
    if request.method == 'GET':
        return admin_service.get_episode(episode_id)
    elif request.method == 'PUT':
        return admin_service.update_episode(episode_id, json.loads(request.get_data(True, as_text=True)))

