set -e

# For running on STRW

cd /home/mcgibbon/Documents/ColibreWebsite
git pull > cron_job.out 2>&1
/home/mcgibbon/Documents/flamingo_website/venv/bin/python make_webpage.py --update >> cron_job.out

mv -f build/papers.html /disks/web1/colibre/
mv -f build/paper_data/* /disks/web1/colibre/paper_data
mv -f build/assets/team/user_map.html /disks/web1/colibre/assets/team
