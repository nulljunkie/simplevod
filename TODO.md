- [ ] Test if Frontend works within and outside the cluster

- [ ] remove redis, mongodb, postgresql, and rabbitmq subchart and use helm depenndeycy to install them, but keep minio since this a custom modified version

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

### frontend

- [ ] reload flicker issues
  1. navbar show login/signup buttons for a moment, even when already logged in
  2. home page reload, says no video found then shows the skeleton, it should start with skeleton and only show video not found when not are really found, this i suspect to be ssr issue
  3. it's the same moment after home page relaod they both login/signup button and no vidoes found show, and both disapear after, navbar start to show upload icon and profile icon, and body start to load the skeleton
  4. spinner while first starting to watch a video, the spinner fickers, it does not spin normally
