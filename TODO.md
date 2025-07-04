#### Iframebreaker

- [x] Build image
- [x] Fix k8s probes keep failing

#### Transcoder

- [x] Add health checks for k8s

#### Upload

- [x] Add support for thumbnail uploads
- [ ] Add k8s probes
- [ ] Startup take too long, might need startup probe, if the cause couldn't be found

#### CoreDNS

- [ ] Implement a mechanism that update corefile with { ingrss host ==> svc (port 80) }

#### Playlist

- [x] Build and run
- [x] If works, Add k8s probes

#### Finalizer

- [x] Build and run
- [x] If works, Add k8s probes
- [x] Update the vidoe update logic to reflect on new schema introduced in upload service

#### Frontend

- [ ] Test if works within and outside the cluster
- [ ] Health checks and k8s probes

#### Videos

- [ ] Overview the implementation
- [ ] Health checks and k8s probes
