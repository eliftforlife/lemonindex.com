/* 11-24 v2 /budget/ (budget_pages.py): type x budget x private/dealer chips, one list of 5 at a time; #t=suv&b=5to10&k=dealer */
(function(){var r=document.querySelector('.bud');if(!r)return;var st={t:'suv',b:'5to10',k:'private'};
var DEF={reg:'5to10',super:'100to200'};
function set(t){return t==='super'?'super':'reg'}
function show(){var s=set(st.t);
r.querySelectorAll('.bud-c[data-b]').forEach(function(c){c.hidden=c.dataset.set!==s});
if(!r.querySelector('.bud-c[data-b="'+st.b+'"][data-set="'+s+'"]'))st.b=DEF[s];
r.querySelectorAll('.bud-l').forEach(function(x){x.hidden=!(x.dataset.t===st.t&&x.dataset.b===st.b&&x.dataset.k===st.k)});
r.querySelectorAll('.bud-c').forEach(function(c){var k=c.dataset.t?'t':c.dataset.b?'b':'k';c.setAttribute('aria-pressed',c.dataset[k]===st[k]?'true':'false')});}
['t','b','k'].forEach(function(k){var m=new RegExp('[#&]'+k+'=([a-z0-9]+)').exec(location.hash);if(m&&r.querySelector('.bud-c[data-'+k+'="'+m[1]+'"]'))st[k]=m[1]});show();
r.addEventListener('click',function(e){var c=e.target.closest('.bud-c');if(!c)return;var k=c.dataset.t?'t':c.dataset.b?'b':'k';st[k]=c.dataset[k];show();
try{history.replaceState(null,'','#t='+st.t+'&b='+st.b+'&k='+st.k)}catch(_){}});})();
