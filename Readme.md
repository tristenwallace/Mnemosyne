# Project Mnemosyne - A groupme bot to send memories

### Useful commands
- `git push stage master` -> deploy to stage
- `git push pro master` -> deploy to prod

### Deployment Urls
- [Stage](https://mnemosyne-bot-stage.herokuapp.com/)
- [Prod](https://mnemosyne-bot-prod.herokuapp.com/)

### Google drive
All images are stored in a google drive  
To post to a groupme group, images must be processed by a groupme process which returns a groupme image url

### Database
A mongoDb database is used to store google drive credentials and weekly goals  
image urls may be stored in mongo one day

### Credentials
no credentials are stored on github
Contact nick for groupme/ googledrive/ heroku credentials

### Set BOT_ID
heroku config:set BOT_ID=[id] --remote stage
