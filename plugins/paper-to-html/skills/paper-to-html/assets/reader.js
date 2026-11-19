const notes = document.getElementById('notes-mode');
const marks = document.getElementById('mark-mode');
notes.addEventListener('click', () => {
  const active = document.body.classList.toggle('notes-only');
  notes.setAttribute('aria-pressed', String(active));
  notes.textContent = active ? '显示对照' : '只看笔记';
});
marks.addEventListener('click', () => {
  const hidden = document.body.classList.toggle('hide-marks');
  marks.setAttribute('aria-pressed', String(!hidden));
});
const tocLinks = [...document.querySelectorAll('.toc a')];
const targets = tocLinks.map(link => document.querySelector(link.hash));
let current = -1;
function updateToc() {
  if (!targets.length) return;
  let next = 0;
  targets.forEach((heading, index) => {
    if (heading.getBoundingClientRect().top < 120) next = index;
  });
  if (next !== current) {
    tocLinks[current]?.removeAttribute('aria-current');
    tocLinks[next].setAttribute('aria-current','location');
    current = next;
  }
}
let waiting = false;
window.addEventListener('scroll', () => {
  if (waiting) return;
  waiting = true;
  requestAnimationFrame(() => { updateToc(); waiting = false; });
}, {passive:true});
updateToc();
