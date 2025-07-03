#### Iframebreaker

- [ ] Build image
- [ ] Fix k8s probes keep failing
- [ ] Update mongodb with status "transcoding" and video duration

#### Transcoder

- [ ] Add health checks for k8s

#### Upload

- [ ] Add support for thumbnail uploads
- [ ] Add k8s probes
- [ ] Startup take too long, might need startup probe, if the cause couldn't be found

#### CoreDNS

- [ ] Implement a mechanism that update corefile with { ingrss host ==> svc (port 80) }

#### Playlist

- [x] Build and run
- [x] If works, Add k8s probes
- [ ]

#### Finalizer

- [x] Build and run
- [x] If works, Add k8s probes
- [x] Update the vidoe update logic to reflect on new schema introduced in upload service
