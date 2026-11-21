# Install this GitHub profile

The target account is `drabkb786`. The profile repository must be public and named `drabkb786`.

1. Create the repository at https://github.com/new?name=drabkb786 and enable **Add a README file**.
2. Copy the contents of this folder into that repository. Include the `.github` directory.
3. Open **Actions → Update profile cards → Run workflow** for the first refresh. Scheduled refreshes run daily.
4. Open https://github.com/drabkb786 to view the Overview.

To publish using GitHub CLI, open a terminal in this extracted folder. Sign into the `drabkb786` account, then run the following commands if the target repository has not been created yet.

```bash
gh auth login
git init -b main
git add .
git commit -m "Create Abdul Basit GitHub profile"
gh repo create drabkb786/drabkb786 --public --description "Abdul Basit | Law student exploring software engineering" --source . --remote origin --push
```

## Update the design

Edit `profile.json`, then regenerate the cards with Python 3.10 or newer.

```bash
python scripts/update_profile.py
```

To rebuild the cards from the saved snapshot without network requests, use this command.

```bash
python scripts/update_profile.py --offline
```

The workflow uses GitHub's automatic `GITHUB_TOKEN` and needs **Contents: write** permission to commit refreshed cards. GitHub may pause scheduled workflows after extended repository inactivity. The manual Run workflow button remains available.

The contribution calendar uses the public GitHub calendar. Aggregate counts follow the profile's public contribution visibility. Language labels describe public repositories. Edit the profile fields whenever your skills or projects change.
