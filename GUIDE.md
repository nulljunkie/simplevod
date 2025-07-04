one root chart: helm/app

subcharts are at helm/app/charts/\*

each subchart has it's own values.yaml at helm/app/chart/<subchart-name>/values.yaml

this values.yaml define all the field with default values, overriden by root helm/app/value.yaml which has acutally values like port number, backends, password, etc

do not ever use helm/app/values-override.yaml this will contain only critical thigns like email address and password

for exmaple ./transcoder is deployed by the subchart ./helm/app/chart/transcoder
