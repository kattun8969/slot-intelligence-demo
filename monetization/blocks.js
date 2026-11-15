/* Standalone monetization renderer. Load only after the site's main content. */
(function(global){
"use strict";
function safeUrl(value){try{const u=new URL(value);return ["https:","http:"].includes(u.protocol)?u.href:null}catch{return null}}
function el(tag,cls,text){const n=document.createElement(tag);if(cls)n.className=cls;if(text)n.textContent=text;return n}
function link(url,label){const a=el("a","monetization-link",label);a.href=url;a.target="_blank";a.rel="noopener noreferrer sponsored";return a}
function render(config,target,kind,viewer){
 if(!target||!config||!config.enabled)return false;
 const page=kind==="home"?"home":"machine";
 if(!config.placements||!config.placements[page])return false;
 const root=el("aside","monetization-block");root.setAttribute("aria-label","サイト運営・広告情報");
 if(viewer&&viewer.adsDisabled)return false;
 const offers=config.affiliate&&config.affiliate.enabled?config.affiliate.offers||[]:[];
 for(const offer of offers){
  const url=safeUrl(offer.url);if(!url||!offer.title||offer.enabled!==true)continue;
  if(Array.isArray(offer.pages)&&!offer.pages.includes(page))continue;
  const card=el("section","monetization-card");card.append(el("span","monetization-pr","PR"));
  const title=el("strong","monetization-title",offer.title);card.append(title);
  if(offer.imageUrl&&safeUrl(offer.imageUrl)){const img=el("img","monetization-image");img.src=safeUrl(offer.imageUrl);img.alt=offer.imageAlt||"";img.loading="lazy";card.append(img)}
  if(offer.description)card.append(el("p","monetization-description",offer.description));
  card.append(link(url,offer.linkLabel||"詳細を見る"));root.append(card);
 }
 const services=config.support&&config.support.enabled?config.support.services||[]:[];
 for(const service of services){
  const url=safeUrl(service.url);if(!url||!service.name||service.enabled!==true)continue;
  const card=el("section","monetization-card monetization-support");
  card.append(el("strong","monetization-title",service.name));
  if(service.description)card.append(el("p","monetization-description",service.description));
  const a=link(url,"開発支援ページを見る");a.rel="noopener noreferrer";card.append(a);root.append(card);
 }
 if(!root.children.length)return false;
 target.append(root);return true;
}
global.SlotMonetization={render,safeUrl};
})(window);
