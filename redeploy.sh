#!/bin/bash
git add -A
git commit -m 'redploying'
git push heroku master
heroku ps:scale web=1
heroku logs -t