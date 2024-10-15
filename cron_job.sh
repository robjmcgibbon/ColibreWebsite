set -e
cd /home/mcgibbon/Documents/flamingo_website/FLAMINGO
/home/mcgibbon/Documents/flamingo_website/venv/bin/python generate_publication_list.py > cron_job.out
/home/mcgibbon/Documents/flamingo_website/venv/bin/python make_webpage.py >> cron_job.out
rm -r /disks/web1/flamingo/*
# Copy to somewhere else on disk, then do a mv
cp -r build/* /disks/web1/flamingo/
rm -r build
