# Music CD ripping on Ubuntu
Create a repeatable process for hundreds of music CDs. This will run on my PC using Ubuntu. The high level process should be as follows.

## Do's and Don't
* Don't: Create multiple methods for each part. My preference is to debug issues as they present. As each Part can encompass many steps, having a second or third method would involve restarting and losing gains from first method.
* Do: Use proper error handling to aid in debuging.
* Don't: Web scraping. Unapproved web scraping is a MAJOR problem that must be avoided. 
* Do: Use API access from well known, reputable services to collect metadata. Free and safe is required. 


## Part 1 

### Rip CDs to high quality FLAC. 
Compression isn't an initial concern, as a later step will create new files using m4a. 
### Collect proper CD meta data
This should include, but is not limited to, Artist, Album Name, Album year, CD #, etc. Enrich ripped CD FLAC files with proper metadata, including CD cover images. 
### If API access is required, please detail what site is necessary. 
Web scraping should be avoided if necessary. 
### Error handling
Provide proper error handling during all steps of this project.

## Part 2 

### Copy FLAC to S3
Create a repeatable process to store FLAC files in AWS S3. This step should account that locally stored FLAC files may eventually be removed. Directly mirroring won't work.

## Part 3

### Local compression and cleanup
Create new m4a files from original FLAC for better compression to be stored locally. Ensure metadata stays in place and isn't overwritten or deleted. Local FLAC files can then be removed.