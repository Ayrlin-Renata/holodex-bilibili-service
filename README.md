# holodex-bilibili-service
proof of concept bilibili livestream status tracker created with the intention of enabling holodex to track bilibili livestreams.

## requirements
in order to run this, you need
- bilibili account
- channel uids for tracked channels

## auth
there is no official, general auth for bilibili, but the well-established state of other apps and services which interface with bilibili is to authenticate using a regular user account. it is not officially supported, but it is unofficially recognized as the way it is done. libraries such as [bilibili_api](https://github.com/Nemo2011/bilibili-api), which is used, and applications are made based on this approach, so it is well supported by the community.

`login_service.py` generates a QR code, which can be scanned with a bilibili app to authenticate. the auth token is then stored and automatically refreshed by the system. no further user interaction is necessary. 

tokens and channel ids (TRACKED_UIDS) are stored in `.env`

## usage 
`main.py` starts scheduled polling of the livestream status as well as the feed posts to detect stream reservations. 
it currently detects:
- livestream title change
- livestream online
- livestream offline
- live announcement post
- reservation post

query scheduler settings are in `main.py`

the output is written to the console and more formally to `stream_events.jsonl`

## other
i am not affiliated with holodex, hololive, COVER, or BiliBili. 