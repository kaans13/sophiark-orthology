"""Global CSS for the card-based result page (theme-safe: tints + borders, no fixed text colors)."""

_RULES = """
:root{--od-shared:#2dd4bf;--od-source:#60a5fa;--od-target:#fbbf24;--od-border:rgba(128,128,128,.28);--od-bg:rgba(128,128,128,.07)}
.od-fade{animation:od-up .55s cubic-bezier(.2,.7,.2,1) both}
@keyframes od-up{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@keyframes od-grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes od-nudge{0%,100%{transform:translateX(0)}50%{transform:translateX(7px)}}
.od-card{border:1px solid var(--od-border);background:var(--od-bg);border-radius:18px;padding:20px 22px;margin:12px 0}
.od-hero{display:grid;grid-template-columns:1fr auto 1fr;gap:20px;align-items:center}
@media(max-width:760px){.od-hero{grid-template-columns:1fr}.od-link{transform:rotate(90deg);margin:6px 0}}
.od-species{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;opacity:.6;margin-bottom:2px}
.od-symbol{font-size:2.2rem;font-weight:800;line-height:1.1}
.od-symbol-sm{font-size:1.5rem}
.od-sub{font-size:.78rem;opacity:.6;font-family:monospace}
.od-desc{font-size:.9rem;opacity:.85;margin-top:4px}
.od-tgt{padding:8px 0;border-bottom:1px dashed var(--od-border)}
.od-tgt:last-child{border-bottom:none}
.od-also{display:inline-block;margin-top:7px;font-size:.8rem;padding:4px 10px;border-radius:8px;background:rgba(96,165,250,.14);border:1px solid rgba(96,165,250,.45)}
.od-link{text-align:center}
.od-arrow{font-size:2.2rem;opacity:.7;animation:od-nudge 1.9s ease-in-out infinite}
.od-arrow-off{animation:none;opacity:.4}
.od-badge{display:inline-block;padding:3px 13px;border-radius:999px;font-size:.8rem;font-weight:700;border:1px solid rgba(45,212,191,.6);background:rgba(45,212,191,.16)}
.od-conf{display:inline-block;margin-top:5px;font-size:.7rem;padding:1px 9px;border-radius:999px;border:1px solid var(--od-border)}
.od-conf-high{background:rgba(34,197,94,.16);border-color:rgba(34,197,94,.5)}
.od-conf-low{background:rgba(251,191,36,.14);border-color:rgba(251,191,36,.5)}
.od-grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin:8px 0 6px}
.od-cat{margin:0}
.od-cat-title{font-size:.95rem;font-weight:700;opacity:.9;margin-bottom:12px}
.od-big{font-size:2.9rem;font-weight:800;line-height:1}
.od-cap{font-size:.78rem;opacity:.7;margin-top:6px;line-height:1.35}
.od-bar{display:flex;height:11px;border-radius:999px;overflow:hidden;background:rgba(128,128,128,.2);margin:16px 0 12px}
.od-seg{height:100%;transform-origin:left;animation:od-grow .9s .25s cubic-bezier(.2,.7,.2,1) both}
.od-seg-shared{background:var(--od-shared)}
.od-seg-source{background:var(--od-source)}
.od-seg-target{background:var(--od-target)}
.od-leg{display:flex;flex-direction:column;gap:4px;font-size:.83rem}
.od-dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:8px}
.od-dot-shared{background:var(--od-shared)}
.od-dot-source{background:var(--od-source)}
.od-dot-target{background:var(--od-target)}
.od-gap{font-size:.86rem;line-height:1.4;padding:11px 13px;border-radius:12px;background:rgba(251,191,36,.12);border:1px solid rgba(251,191,36,.4)}
.od-muted{font-size:.86rem;opacity:.6}
.od-section-title{font-size:1.2rem;font-weight:700;margin:26px 0 4px}
.od-evlegend{font-size:.78rem;opacity:.85;margin:4px 0 10px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.od-group{border:1px solid var(--od-border);border-radius:14px;margin:10px 0;padding:4px 14px}
.od-group-shared{--grp:var(--od-shared)}
.od-group-source{--grp:var(--od-source)}
.od-group-target{--grp:var(--od-target)}
.od-group>summary{cursor:pointer;padding:10px 0;font-weight:600;list-style:none}
.od-group>summary::-webkit-details-marker{display:none}
.od-group>summary::before{content:"\\25B8";display:inline-block;margin-right:9px;transition:transform .2s}
.od-group[open]>summary::before{transform:rotate(90deg)}
.od-count{opacity:.6;font-weight:500;margin-left:6px}
.od-terms{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:8px;max-height:400px;overflow-y:auto;padding:6px 2px 12px}
.od-term{border:1px solid var(--od-border);border-left:3px solid var(--grp);border-radius:10px;padding:9px 12px;background:var(--od-bg);transition:transform .15s,background .15s}
.od-term:hover{transform:translateY(-2px);background:rgba(128,128,128,.13)}
.od-term-name{font-size:.87rem;line-height:1.3}
.od-term-meta{display:flex;flex-wrap:wrap;gap:5px;align-items:center;margin-top:6px}
.od-id{font-family:monospace;font-size:.7rem;opacity:.55;margin-right:3px}
.od-sep{opacity:.4;font-size:.75rem}
.od-ev{font-size:.66rem;font-weight:700;padding:1px 7px;border-radius:6px;letter-spacing:.03em;border:1px solid var(--od-border)}
.od-ev-exp{background:rgba(34,197,94,.2);border-color:rgba(34,197,94,.55)}
.od-ev-inf{background:rgba(96,165,250,.2);border-color:rgba(96,165,250,.55)}
.od-ev-auth{background:rgba(251,191,36,.18);border-color:rgba(251,191,36,.55)}
.od-ev-iea{background:rgba(128,128,128,.2);border-color:rgba(128,128,128,.5)}
.od-empty{opacity:.55;font-size:.86rem;padding:8px 2px}
.od-note{font-size:.8rem;opacity:.7;text-align:center;padding:18px 8px 6px}
.od-kvs{display:grid;grid-template-columns:auto 1fr;gap:6px 18px;font-size:.85rem}
.od-kvs span:nth-child(odd){opacity:.6}

.od-header{display:flex;align-items:center;gap:18px;margin:4px 0 14px}
.od-logo{height:68px;width:auto;flex:none}
.od-app-title{font-size:2.5rem;font-weight:800;line-height:1.05;letter-spacing:-.01em}
.od-app-title span{background:linear-gradient(90deg,var(--od-shared),var(--od-source));-webkit-background-clip:text;background-clip:text;color:transparent}
.od-app-sub{font-size:.95rem;opacity:.75;margin-top:6px;max-width:720px}
@media(max-width:600px){.od-header{flex-direction:column;align-items:flex-start}.od-app-title{font-size:2rem}}
.od-footer{border:1px solid var(--od-border);background:var(--od-bg);border-radius:20px;padding:24px 26px;margin:38px 0 8px}
.od-foot-main{display:flex;align-items:center;gap:14px}
.od-foot-logo{height:44px;width:auto}
.od-foot-name{font-size:1.15rem;font-weight:800}
.od-foot-tag{font-size:.83rem;opacity:.7;margin-top:2px}
.od-foot-by{margin-top:16px;font-size:.95rem}
.od-foot-try{margin-top:18px;font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;opacity:.6}
.od-prods{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px;margin-top:8px}
.od-prod{display:flex;flex-direction:column;gap:5px;padding:14px 16px;border:1px solid var(--od-border);border-radius:14px;text-decoration:none;color:inherit;transition:transform .15s,background .15s,border-color .15s}
.od-prod:hover{transform:translateY(-3px);background:rgba(45,212,191,.09);border-color:rgba(45,212,191,.55)}
.od-prod span{font-size:.83rem;opacity:.75;line-height:1.35}
.od-prod em{font-style:normal;font-size:.8rem;font-weight:700;color:var(--od-shared)}
.od-foot-links{margin-top:14px}
.od-btn{display:inline-block;padding:6px 16px;border-radius:999px;border:1px solid var(--od-border);text-decoration:none;color:inherit;font-size:.83rem;font-weight:600;transition:background .15s}
.od-btn:hover{background:rgba(128,128,128,.15)}
.od-foot-copy{margin-top:16px;font-size:.74rem;opacity:.55}
"""

CSS = "<style>" + " ".join(_RULES.split()) + "</style>"