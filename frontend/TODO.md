### Navbar

- [ ] Reload while on `/`, creates a filcker, login and sign up button appear for fraction of time, then the upload and profile buttons appear, also the upload button style changes from solid to outlined
- [ ] Reload while on `/profile`, profile image changes from the email (e.g. JA for jackdorsey@gmail.com) to US which stands for User, i think reload the profile page trie to fetch profile info, but without them the state user.email is set to User which is i guess is the default
- [ ] The upload progress indicator switch in to 0% after it reaches 100% for couple of seconds before it's removed

- [ ] check out ~/composables/useApi.ts and ~/types/api.ts there is ApiResponse i both of them, why is that? or simply a miss understanding that to be resolved?
- [ ] my video store is outdated useApi composable has been updated and types also have been updated, update my videos store to this new useApi composable, as for video types, yuou can also update them if needed but beware that the current ones align with my backend stream api schemas
- [ ] redesign my home page with video list and watch page to be kinda similar to youtube following these structure in these 2 wireframes, make sure in watch page, watch queue at right side is just the list of all videos refetched, you don't even have to remove the current video that's playing, because in teh feature i will have a dedicated endpint for this watch queue, but for now focus on design that follows the whole design and color scheme of my application

## Understanding - Satisfaction

##### components/ui/Modal.vue

- [x] understand
- [x] satisfied

##### components/ui/Input.vue

- [x] understand
- [x] satisfied

##### components/ui/Button.vue

- [x] understand
- [x] satisfied

##### components/auth/LoginModal.vue and RegisterModal.vue

- [x] understand
- [x] satisfied

##### components/layout/Navbar/\*.vue

- [x] understand
- [x] satisfied

##### components/ui/Dropdown.vue

- [x] understand
- [x] satisfied

##### components/upload/UploadModal.vue

- [x] understand
- [ ] order of things: video,thumbnail,title,description (text field),visiblity Need a nice drag and drop for video and thunbmail
- [ ] satisfied

##### components/upload/Dropdown.vue

- [x] understand
- [x] satisfied
- [x] what custom-scrollbar class in the body
- [x] checkout "Clear Completed" button

##### components/upload/Progress.vue

- [x] understand
- [x] satisfied

### CONTINUE

layout/Footer.vue
video/\*
pages/\*

##### pages/index.vue

- [ ] understand how watches fetches new videos on page changes
- [ ] onBeforeUnmount to think about
- [ ] fix: loading the page shows emty state then skeleton, then the videos

##### pages/ui/VideoThumbnail.vue

- [x] understand
- [x] satisfied

##### pages/video/VideoCard.vue

- [x] understand
- [x] satisfied
- [x] add back the video's real duration

##### pages/video/VideoCardSidebar.vue

- [x] understand
- [x] satisfied
- [x] add back the video's real duration

##### pages/ui/VideoOwner.vue

- [x] understand
- [x] satisfied
- [ ] pass username, after being implemeted to include the response

##### pages/watch/[id].vue

- [x] understand
- [x] satisfied
- [ ] pass username to VideoOwner

### z indecies:

player controllers: z-10
dropdowns: 20
modals: 30
