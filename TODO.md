- [ ] Test if Frontend works within and outside the cluster
- [ ] Minio init container to wait to rabbitmq
  - if you examinine values.yaml and README.md in the minio subchart, ??????????????????????????????? using addtional env, and config, to pass value to wait-for-rabbitmq init container or just harcore the values like rabbitmq host and port to field initContainer:
- [ ] remove redis, mongodb, postgresql, and rabbitmq subchart and use helm depenndeycy to install them, but keep minio since this a custom modified version
- [ ] upload service bad design create an instance and new connection to minio, mongo, and redis, create new instances of core services and classes at each time something happen, like just a minor regular health check? that's bad isn't need i think a single instance that create first and the dependency injection keeps passing that single instance for the hanlders and methods? the current implemenetation has one adnvantage it covers also the retry logic, by creating new connection each time? do we might need to go hyprid, mix of both approches?? or simple have a singleton or factory pattern??? then implementing a retry logic directly and concretely

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
    --> if the subchart's own values.yaml does not define debug: with a value, use the the global from root chart's values.yaml
