## FRONTEND

- [ ] Test if Frontend works within and outside the cluster

## HELM

- [ ] remove redis, mongodb, postgresql, and rabbitmq subchart and use helm depenndeycy to install them, but keep minio since this a custom modified version

## LOGGING

- [ ] make sure my apps

  - upload
  - users
  - users-celery
  - auth
  - iframebreaker
  - playlist
  - videos
  - transcoder
  - finalizer
    --> if the subchart's own values.yaml does not define debug: with a value, use the the global from root chart's values.yaml, this can be done with using "default" helm function

    if you checkout users service and celery, you'll see that maybe i think, the logger is create twice, that should not happen?? if you check main you'll see logger creatin in top and in bottom also, i wish that that does not happens to celery tasks also

    and health checks in all my apps should be only shows with DEBUG enabled, other important business logic use INFO (like actual http requests, and other things)

## SYNTHETIC DATA

create 8 documents that i can copy paste to mongo-express that to fill database with fake videos, need to use same documents and schema used by upload service @uplaod same what saves to db, for username you can use these 3 and switch between them (imad148499, kingslayer4, badjoke1000) leave thubnail url empty, write these documents to a file
