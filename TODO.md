## FRONTEND

- [ ] Test if Frontend works within and outside the cluster
- [ ] Fix progress indicator, showing 0% after finish, should stay at 100% for a couple seconds then vanish

## STATUS

- [ ] Use configmaps and secrets, and pass values to them dynamically not hardcoded, see how other similar servies implement it

- [ ] have a unified videos status

  - uploaded
  - processing
  - transcoding
  - published
  - failed

  upload service alreay has access to mongo, so it will set status to "uploaded"
  iframbreaker, does not have access to mongo, so need to implement publishing to status queue w/o affecting or chaning much the existing logic, when message for a video is received by a consumer, that status for that key is set to "processsing", and can be changed after ward if ffprobe fails, or failed to published result messages, if all good status stays in "processing"
  transocoder when picks on new video set status to "transcoding" and never changed unless an error (e.g. failed to create the jobs, etc)
  playlist is not concerned with this
  finalizer alreay as access to mongo, so itself does set to "published" if all well

  all this should be done, go through step by step don't not rush it, do static analysis regulartly to make sure things are in order

  videos, implements and webhook or short polling for receving status live in teh frontend, see teh better aproach to taggle this, video does not implmeted get my won videos yet,
