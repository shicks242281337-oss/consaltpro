// КонсалтПро — настройка ссылок на релизы GitHub и подтягивание версии.
// OWNER/REPO указываются один раз здесь; после создания репозитория
// меняется значение REPO, если понадобится.
const OWNER = "shicks242281337-oss";
const REPO = "consaltpro";

const releaseUrl = `https://github.com/${OWNER}/${REPO}/releases/latest`;
const repoUrl = `https://github.com/${OWNER}/${REPO}`;

const winUrl = `${releaseUrl}/download/ConsaltPro.exe`;
const apkUrl = `${releaseUrl}/download/ConsaltPro.apk`;

function applyLinks() {
  const set = (id, href) => {
    const el = document.getElementById(id);
    if (el) el.setAttribute("href", href);
  };

  set("dl-win", winUrl);
  set("dl-apk", apkUrl);
  set("dl-src", repoUrl);
  set("releases-link", releaseUrl);
  set("foot-repo", repoUrl);
  set("foot-releases", releaseUrl);

  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
}

async function loadReleaseTag() {
  const tagEl = document.getElementById("release-tag");
  if (!tagEl) return;
  try {
    const response = await fetch(
      `https://api.github.com/repos/${OWNER}/${REPO}/releases/latest`
    );
    if (!response.ok) return;
    const release = await response.json();
    if (release.tag_name) tagEl.textContent = release.tag_name;
    if (release.html_url) {
      const link = document.getElementById("releases-link");
      if (link) link.setAttribute("href", release.html_url);
    }
  } catch (err) {
    // GitHub API недоступен — остаётся текст «—».
  }
}

applyLinks();
loadReleaseTag();
