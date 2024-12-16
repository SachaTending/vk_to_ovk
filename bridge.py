"""
    VK to OpenVK bridge version 0.0.7
    Copyright (C) 2024  TendingStream73

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""

from fastapi import FastAPI, APIRouter, Form
from httpx import get, post
from loguru import logger
from starlette.requests import Request
import httpx
from starlette.responses import StreamingResponse, Response
from starlette.background import BackgroundTask
from json import loads, dumps

app = FastAPI()
methods = APIRouter(prefix="/method")

from typing import TypedDict, Annotated

class UserInfo(TypedDict):
    id: int
    first_name: str
    last_name: str
    is_closed: bool
    can_access_closed: bool
    photo_100: str
    photo_50: str
    online: int

class LongPoll(TypedDict):
    ts: int
    key: str
    server: str

def get_user(token: str) -> UserInfo:
    return post(f"https://ovk.to/method/Users.get?access_token={token}&fields=photo_100,photo_50", data={'access_token': token}).json()['response'][0]

def get_longpoll(token: str) -> LongPoll:
    return get(f"https://ovk.to/method/messages.getLongPollServer?access_token={token}").json()['response']

def kw_to_dict(k) -> dict:
    print(k)
    return k

def get_api(method: str, token: str, uagent: str="", **kwargs) -> dict:
    kwargs = kw_to_dict(kwargs)
    r =  post(f"https://ovk.to/method/{method}?access_token={token}", headers={"user-agent": uagent}, data=kwargs).json()
    print(r)
    return r

@methods.post("/execute.getCommentsNew")
async def getCommentsNew(owner_id: Annotated[int, Form()], item_id: Annotated[int, Form()], need_likes: Annotated[int, Form()], access_token: Annotated[str, Form()]):
    return get_api("wall.getComments", access_token, owner_id=owner_id, post_id=item_id, need_likes=need_likes)

@methods.post("/execute.getUserInfo")
async def getUserInfo(access_token: Annotated[str, Form()]):
    ud = get_user(access_token)
    #print(ud)
    resp = {
        "response": {
            "profile": {
                "id": ud['id'],
                "first_name": ud['first_name'],
                "last_name": ud['last_name'],
                "photo_50": "https://kaslana.ovk.to/hentai/de/de4d3aed069f7eb088336576ec7e62e541ef9dd4486ee94d90a1a9f5ac92ea86ab6a386c65252b5aa539f08f71a348ea6d9620227ae81961a334810cb89139b7_cropped/miniscule.gif",
                "photo_100": "https://kaslana.ovk.to/hentai/de/de4d3aed069f7eb088336576ec7e62e541ef9dd4486ee94d90a1a9f5ac92ea86ab6a386c65252b5aa539f08f71a348ea6d9620227ae81961a334810cb89139b7_cropped/tiny.gif",
                "status": "Unknown",
                "exports": {},
                "verified": 1,
            },
            "info": {
                "settings": [],
                "debug_available": True,
                "support_url": "https://ovk.to",
                "intro": 0
            },
            "time": 1500477243
        }
    }
    return resp

@methods.post("/execute.getFriendsAndLists")
async def get_friends(access_token: Annotated[str, Form()], fields: Annotated[str, Form()]=""):
    return get_api("Friends.get", token=access_token, fields=fields)

@methods.post("/audio.search")
async def audio_search(q: Annotated[str, Form()], count: Annotated[int, Form()], access_token: Annotated[str, Form()]):
    r = get_api("audio.search", token=access_token, q=q, count=count)
    for i in range(r['response']['count']):
        #r['response']['items'][i]['aid'] = r['response']['items'][i]['id'] = int(b64decode(r['response']['items'][i]['unique_id']).decode())
        pass
    return r

@methods.post("/execute.getFullProfileNewNew")
async def getFullProfileNewNew(): # why the fuck this method has suffix NewNew?
    return {
        
    }

@methods.post("/audio.add")
async def audio_add(access_token: Annotated[str, Form()], audio_id: Annotated[int, Form()], owner_id: Annotated[int, Form()]):
    return get_api("audio.add", access_token, audio_id=audio_id, owner_id=owner_id)

@methods.post("/audio.delete")
async def audio_add(access_token: Annotated[str, Form()], audio_id: Annotated[int, Form()], owner_id: Annotated[int, Form()]):
    return get_api("audio.delete", access_token, audio_id=audio_id, owner_id=owner_id)


async def ihatevkscript1(): # returns data needed for long poll
    r = {
        "c": {},
        "s": {
            "server": "0.0.0.0",
            "key": "LONGPOLL_IS_BROKEN",
            "ts": 0
        },
        "fo": {
            "online": [],
            "online_mobile": []
        }
    }
    # Fix server address
    r['s']['server'] = r['s']['server'].removeprefix("https://").replace("ovk.to", "api.vk.com")
    return r

predefinedVkScript = {
    "return {c:API.getCounters(),s:API.messages.getLongPollServer({use_ssl:1}),fo:API.friends.getOnline({online_mobile:1})};": ihatevkscript1 
}
@methods.post("/account.getPushSettings")
async def getPushSettings():
    return {
        "response": {
            "conversations": {
                "items": []
            }
        }
    }



@methods.post("/execute")
async def execute_vkscript(access_token: Annotated[str, Form()], code: Annotated[str, Form()]):
    p = predefinedVkScript.get(code, None)
    if p != None:
        r = await p()
        print("resp:", r)
        return {"response": r}
    return {}

class Audio(TypedDict):
    artist: str
    duration: int
    id: int
    owner_id: int
    title: str
    url: str


@methods.post("/audio.get")
@logger.catch
def audio_get(access_token: Annotated[str, Form()]):
    a = get_api("Audio.get", token=access_token, owner_id=17863)['response']['items']
    items: list[Audio] = []
    for i in a:
        items.append({
            'artist': i['artist'],
            'title': i['title'],
            'duration': i['duration'],
            'id': i['id'],
            'owner_id': i['owner_id'],
            'url': i['url']
        })
    return {
        'response': {
            'count': len(items),
            'items': items
        }
    }

@methods.post("/groups.get")
@logger.catch
def groups_get(access_token: Annotated[str, Form()]):
    ret = get_api("Groups.get", token=access_token, fields="verified, has_photo, photo_max_orig, photo_max, photo_50, photo_100, photo_200, photo_200_orig, photo_400_orig, members_count, can_suggest, suggested_count".replace(" ", ""))['response']['items']
    for i in range(len(ret)):
        ret[i]['is_closed'] = int(ret[i]['is_closed'])
    return {
        "response": {
            "count": len(ret),
            "items": ret
        }
    }

@methods.post("/execute.getNotifications")
async def getnotif(access_token: Annotated[str, Form()]):
    return get_api("notifications.get", token=access_token)

@methods.post("/execute.wallPost")
async def wall_post(message: Annotated[str, Form()], access_token: Annotated[str, Form()]):
    return get_api("wall.post", token=access_token, message=message, owner_id=17863)

@methods.post("/execute.getNewsfeedSmart")
@logger.catch
def getnewsfeed(count: Annotated[int, Form()], start_from: Annotated[int, Form()], access_token: Annotated[str, Form()], feed_type: Annotated[str, Form()]=''):
    if feed_type == 'recommended':
        nf = get_api("Newsfeed.getGlobal", token=access_token, count=count, start_from=start_from)
    else:
        nf = get_api("Newsfeed.get", token=access_token, count=count, start_from=start_from)
    #open("nf.json", "w").write(dumps(nf, indent=4))
    uids = []
    gids = []
    for i in nf['response']['items']:
        author_id = i['from_id']
        if author_id < 0:
            author_id = 0 - author_id
            if not (author_id in gids): gids.append(str(author_id))
        else:
            if not (author_id in uids): uids.append(str(author_id))
    users = get_api("users.get", access_token, user_ids=",".join(uids), fields="photo_50,sex,photo_100,last_seen")
    groups = get_api("groups.getById", access_token, group_ids=",".join(gids), fields="photo_50,verified,photo_100")
    nf['response']['profiles'] = users['response']
    nf['response']['groups'] = groups['response']
    return nf

app.include_router(methods)

async def token_req(request: Request):
    url = httpx.URL(path="/token", query=request.url.query.encode("utf-8"))
    client = httpx.AsyncClient(base_url="https://ovk.to")
    rp_req = client.build_request(request.method, url,
                                  headers=request.headers.raw,
                                  content=await request.body())
    rp_resp = await client.send(rp_req)
    c = loads(await rp_resp.content)
    c['secret'] = '123'
    c = dumps(c, indent=4)
    return Response(
        c,
        status_code=rp_resp.status_code,
        headers=rp_resp.headers,
    )

app.add_route("/token",
              token_req, ["GET", "POST"])
