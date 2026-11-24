/* 11-24 /budget/ chips (budget_pages.py) */
(function(){var r=document.querySelector('.bud');if(!r)return;var b='10k',s='all';
function show(){r.querySelectorAll('.bud-l').forEach(function(x){x.hidden=!(x.dataset.b===b&&x.dataset.s===s)});
r.querySelectorAll('.bud-c').forEach(function(c){c.setAttribute('aria-pressed',(c.dataset.b?c.dataset.b===b:c.dataset.s===s)?'true':'false')});}
var m=/b=(\w+)/.exec(location.hash);if(m&&r.querySelector('.bud-l[data-b="'+m[1]+'"]'))b=m[1];var n=/s=(\w+)/.exec(location.hash);if(n&&r.querySelector('.bud-l[data-s="'+n[1]+'"]'))s=n[1];show();
r.addEventListener('click',function(e){var c=e.target.closest('.bud-c');if(!c)return;if(c.dataset.b)b=c.dataset.b;else s=c.dataset.s;show();
try{history.replaceState(null,'','#b='+b+(s!=='all'?'&s='+s:''))}catch(_){}});})();
