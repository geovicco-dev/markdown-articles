import streamlit as st

st.set_page_config(page_title='FileCloud as DVC Store', layout='wide')
st.title('Using Personal Cloud as DVC Remote')

st.markdown(
"""

From a data science perspective, versioning code, and it's underlying data and models, is crucial in machine learning projects and in line with [MLOps principles](https://ml-ops.org/content/mlops-principles). By versioning all three parts of our workflow, we ensure reproducibility, facilitate collaboration, and maintain an audit trail of our project's evolution.

I recently did a workshop to demonstrate how [DVC](https://dvc.org/doc) can be integrated in large-scale ML projects mainly for the purpose of [versioning datasets and models](https://dvc.org/doc/use-cases/versioning-data-and-models). For the demo, I had configured Google Drive folder as a [`dvc remote`](https://dvc.org/doc/command-reference/remote#remote) using which people could pull the versioned data from the git repository. However, in order to have a shareable git repository for the workshop, the dvc remote had to be accessible by anyone with access to the repository. Due to limited time available for preparation, the only way was to have the repository contain credentials for that folder. Alternatively, I could have setup a [GCP account](https://dvc.org/doc/user-guide/data-management/remote-storage/google-drive#google-drive), but that felt a bit too involved for the purpose of a simple demo. 

This led me to thinking about a scenario where the data exceeded 15GB of storage, requiring me to pay for cloud storage costs. The only problem is that cloud storage services are expensive and there are data privacy issues. In this context, I have been exploring FileCloud Community Edition as an on-premise cloud storage replacement for Google Drive and OneDrive. This article will explore leveraging FileCloud Community Edition to create an on-premise cloud infrastructure, made accessible via a permanent Cloudflare Tunnel on a personally hosted website. This approach allows us to create a DVC remote storage that's accessible via the internet without any storage costs, is free to use, and easy to set up. 
## Solution
Based on my experience with the workshop, the need for a locally hosted file server that is accessible via internet with some form of authentication was ideal. In theory, this means the `remote` storage configured for every DVC-based project will point to the same folder. This is what the IT people call an `on-premise cloud storage solution`.

In pursuit of this solution, I came across [FileCloud Community Edition](https://www.filecloud.com/supportdocs/fcdoc/latest/server/filecloud-administrator-guide/about-filecloud-for-administrators) for creating a self-hosted data server and access it remotely via a [cloudflare tunnel](https://developers.cloudflare.com/pages/how-to/preview-with-cloudflare-tunnel/). This setup provides amazing flexibility and control over project data. As an administrator, FileCloud lets you configure access to data by creating groups and users, restricting folder access and storage limits based on these permissions. This results in a powerful, customisable, and secure on-premise cloud server that can be configured as a DVC remote for any ML project. 

The ultimate perk of this approach lies in its ability to provide the freedom to code from anywhere in the world, on any device, while our data remains versioned on our personal on-premise cloud. This is possible because we can map our personal cloud storage as a network drive on our computer, making sure we always have access to the different versions of data and models just like your code with git. All this without worrying about storage costs or data privacy issues. This setup eliminates the need to upload sensitive or large datasets to third-party cloud services, which is particularly valuable in enterprise or research settings where data privacy and local infrastructure utilisation are priorities.

This approach not only enhances reproducibility and collaboration potential but also makes the most of existing resources (thinking of an old unused laptop or a Raspberry Pi...) to create a powerful, flexible, and cost-effective data versioning solution.

---
## Demo: OpenEarthMap Segmentation Challenge

In this next part, lets explore how we can integrate DVC into a typical deep learning workflow. We will be working with [OpenEarthMap](https://github.com/bao18/open_earth_map/tree/main) dataset for multi-class semantic segmentation for land cover mapping.
> OpenEarthMap is a benchmark dataset for global high-resolution land cover mapping. OpenEarthMap consists of 5000 aerial and satellite images with manually annotated 8-class land cover labels and 2.2 million segments at a 0.25-0.5m ground sampling distance, covering 97 regions from 44 countries across 6 continents. Land cover mapping models trained on OpenEarthMap generalise worldwide and can be used as off-the-shelf models in a variety of applications.

The objective is to configure a DVC remote storage that is hosted on our personal cloud server exposed via a domain using cloudflare tunnels. To do this, we will:
1. Setup FileCloud Community Edition on our local host,
2. Allow remote access to localhost using cloudflare tunnels, and
3. Mount cloud storage as a network drive and map it as a dvc remote storage.

### 1. FileCloud Install and Setup

##### Register and Download
First step is to register and download [FileCloud Community Edition](https://ce.filecloud.com/#communityTrial). It comes with a 1 year license that apparently is renewable indefinitely. Navigate to the [portal link](https://portal.getfilecloud.com) after signing up and email verification. Use the `Download Now` button and follow the next steps to download the license file.

![Image](../images/Pasted%20image%2020240705161417.png)

##### Install
At the time of install I was working on Ubuntu 22.04.2 LTS and the following instructions were used:
```shell
curl -fsSL https://pgp.mongodb.com/server-6.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg --dearmor
 
curl -fsSL https://repo.filecloudlabs.com/static/pgp/filecloud.asc | sudo gpg -o /usr/share/keyrings/filecloud.gpg --dearmor
 
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
 
echo "deb [ arch=amd64 signed-by=/usr/share/keyrings/filecloud.gpg ] https://repo.filecloudlabs.com/apt/ubuntu jammy/filecloud/23.232 main" | sudo tee /etc/apt/sources.list.d/filecloud.list
 
sudo apt-get update -y
 
sudo apt-get install apache2 mongodb-org pigz -y
sudo apt install -y --no-install-recommends php8.2*
sudo apt-get install filecloud -y
```
##### Admin Login
After installation, we will configure our admin dashboard. Follow the getting started instructions for admins [here](https://www.filecloud.com/supportdocs/fcdoc/latest/server/filecloud-administrator-guide/filecloud-site-setup/administrator-settings/logging-in).

If things have gone right, typing `localhost/admin` inside a web browser will land you to the admin login screen (see below). Similarly, typing `localhost/user` redirects you to the user login screen.
> Admin Credentials - `admin` | `password`
![[Pasted image 20240705163646.png]]
##### Validate License
After logging in as an admin, we will be prompted to provide a license file.
![[Pasted image 20240705164004.png]]

##### Update Storage Path
Next, we want to edit the storage path where we want FileCloud to save and retrieve data from. Go to `Settings` > `Storage` > `My Files` and edit `Storage Path` field. 
> For my purpose, I am using `/mnt/d/FileCloud` pointing to a folder called `FileCloud` inside my D drive. 

Click the `Check Path` to verify if the path is valid and then save changes. 

##### Create a User
Next we will create a user called `test-dvc` that will be able to access the cloud storage using it's credentials specified while creating.

Go to `Users` > `+ Add User` > `Create` 
![[Pasted image 20240705165639.png]]

### 2. Configure Localhost and Cloudflare Tunnel 
[Download and install `Cloudflared`](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/)

Create a Temporary Tunnel
```shell
cloudflared tunnel --url http://localhost
``` 
![[Pasted image 20240705180148.png]]
A temporary tunnel is now available via a URL - see the same login screen as our localhost.
![[Pasted image 20240705180436.png]]
However, this is only temporary in the sense that once the terminal window running the `cloudflared tunnel` command is closed, this URL will no longer be valid. As cool as this is, it still doesn't provide a permanent cloud storage we are after.

To create a permanent tunnel, the steps are a bit more involved but straightforward enough and can be followed from multiple online resources as well as the [official documentation](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-remote-tunnel/).

Based on the instructions outlined in the official documentation, I was able to create a permanent tunnel that points my localhost to a subdomain on a publicly hosted domain name so that whenever I or someone who has the credentials to access the webpage `https://dvcstore.geovicco.xyz` will see the same login screen as above. As long as I, as an admin have provided the user with the right level of access, they will be able to use their credentials to login and start adding and deleting files like they would with their OneDrive or GoogleDrive.
![[Pasted image 20240705182038.png]]
Finally, now with a permanent web address pointing to our cloud storage, we can edit the `Server URL` insde our FileCloud admin settings to point to [login page](https://dvcstore.geovicco.xyz).
![[Pasted image 20240705182650.png]]
Finally, we can login using the user credentials created earlier. The login screen looks like the image below. We can there is 1TB of storage assigned to this user (configurable inside admin dashboard). Before proceeding to the next section we will install desktop apps as shown on the top right area of the login screen.
![[Pasted image 20240706001920.png]]
	The only app required to mount the cloud as a DVC remote is [FileCloud Drive](https://www.filecloud.com/additional-downloads/#drive). Enter the `Server URL` and user account credentials.
![[Pasted image 20240706004003.png]]
For `3. General Settings` make sure to take note of the mount point. This mount is where all your cloud data will be stored. If the admin has given this user full access, this drive can be used to not only read data but also write data - which is what we want when pushing and pulling our datasets and models using DVC.
![[Pasted image 20240706004130.png]]
### 3. Configure cloud storage as dvc remote

In last part of this already very long article, we will bring everything together. The cloud storage can be mounted as a local driver on our computer and configured as a dvc remote. We will use this remote for versioning a fairly large dataset and a deep learning model trained from it. We are so close to our goal, so please stick around! 

Create Project Folder and Setup Virtual Environment
```bash
mkdir -p dvc-filecloud-demo && cd dvc-filecloud-demo 
pip install uv && uv venv --python=3.10 .venv && source ./.venv/bin/activate
```
Initialise Git Repository and Create Project Files
```shell
git init .
mkdir -p data
touch .gitignore readme.md  app.py params.yaml requirements.txt notebook.ipynb
```
Edit `requirements.txt` 
```text
pandas==2.2.2
nbconvert==7.16.4
ipykernel==6.29.4
jupyter==1.0.0
ipywidgets==8.1.3
matplotlib==3.9.0
rioxarray==0.15.0
dvc==3.51.2
ensure==1.0.4
python-box==7.1.1
zenodo-get==1.6.1
scikit-learn==1.5.1
albumentations==1.4.8
joblib==1.4.2
numpy==1.26.4
PyYAML==6.0.1
segmentation_models_pytorch==0.3.3
setuptools==68.2.2
torch==2.3.0
lightning==2.2.5
tensorboardx==2.6.2.2
torch-tb-profiler==0.4.3
onnx==1.16.1
```
Install dependencies
```bash
uv pip install -r requirements.txt
```

Before using DVC, lets create a remote repository using GitHub's CLI tool [`gh`](https://github.com/cli/cli)
```bash
gh repo create OpenEarthMap --public -d "Git repository for working with OpenEarthMap landcover classification and segmentation dataset. The purpose is to create a reporoducible workflow for training deep learning models and integrate them with DVC for managing datasets and models versioned on an on-premise cloud storage server using FileCloud."
```
![[Pasted image 20240705131043.png]]
Next, lets specify the above repo as the `git remote` for publishing our code.
```bash
git remote add origin https://github.com/geovicco-dev/OpenEarthMap.git
```

#### Download Data and Prepare Training Metadata
The first stage of the workflow will involve the following steps:
- [ ] Download and extract data using `zenodo_get` command,
- [ ] Aggregate data from different splits and filter images with labels, and
- [ ] Split image/label pairs into training, validation, and test sets.
- [ ] Save metadata with different splits as a csv

The entire workflow for this stage is contained inside the `src/data_ingestion.py` file. The following parameters inside `params.yaml` are used during processing:
	```
```json
doi: 10.5281/zenodo.7223446 # Digital Object Identifier
out_dir: data
metadata_file: data/metadata.csv
train_test_val_split:
- 0.75 # Training
- 0.15 # Validation
- 0.10 # Test
random_seed: 37
```

The workflow uses `doi` of the dataset and downloads it using `zenodo_get` command from the terminal, saves it and extracts it's contents inside `out_dir` directory. The downloaded files are then aggregated into a pandas DataFrame and only those images that have corresponding labels present are kept, the rest are removed to save some space (these are useless for our purpose since they cannot be used during validation or testing). The remaining image/label pairs are then split into different sets using the `train_test_val_split` and `random_seed`. The resulting pandas DataFrames are then combined and finally saved to path specified by `metadata_file` parameter.
#### Versioning Data using DVC

DVC's efficient storage mechanism, which only tracks changes between versions of the files being monitored, is particularly beneficial for large datasets like OpenEarthMap. At the end of stage one, the `data` folder has roughly 9.8 GB worth of files. This is where we will start integrating DVC into our workflow.
```shell
erd data -H -L 1 -y inverted
```
![[Pasted image 20240704161634.png]]
We will start by creating a folder called `dvcstorage` inside the mounted cloud drive.
![[Pasted image 20240706004713.png]]
##### Initialise DVC
```shell
dvc init
```
##### Track Data Folder
```
dvc config core.autostage true
dvc add data
```
##### Configure Remote
```
dvc remote add --default filecloud ~/cloudmount/My\ Files/dvcstorage
```
##### Push to Remote
```shell
dvc push -r filecloud
```
![[Pasted image 20240706005747.png]]
Now when we check our `~/cloudmount` folder, we will see that versioned `data` directory has been successfully pushed to `dvc remote`. 
![[Pasted image 20240706105726.png]]
Lets push these changes to git so that next time we do dvc pull followed by git clone or git pull, all contents of the `data` folder are retrieved from the dvc `remote`.
```shell
git add . && git commit -m "added dvc remote and tracked data directory"
git push -u origin main
```

"""
)