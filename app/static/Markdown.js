(function(){function e(e){return e.replace(/<[^>]*>?/gi,t)}function t(e){return e.match(s)||e.match(o)||e.match(a)?e:""}function i(e){if(""==e)return"";var t=/<\/?\w+[^>]*(\s|$|>)/g,i=e.toLowerCase().match(t),n=(i||[]).length;if(0==n)return e;for(var r,s,o,a="<p><img><br><li><hr>",l=[],h=[],c=!1,u=0;n>u;u++)if(r=i[u].replace(/<\/?(\w+).*/,"$1"),!(l[u]||a.search("<"+r+">")>-1)){if(s=i[u],o=-1,!/^<\//.test(s))for(var d=u+1;n>d;d++)if(!l[d]&&i[d]=="</"+r+">"){o=d;break}-1==o?c=h[u]=!0:l[o]=!0}if(!c)return e;var u=0;return e=e.replace(t,function(e){var t=h[u]?"":e;return u++,t})}var n,r;"object"==typeof exports&&"function"==typeof require?(n=exports,r=require("./Markdown.Converter").Converter):(n=window.Markdown,r=n.Converter),n.getSanitizingConverter=function(){var t=new r;return t.hooks.chain("postConversion",e),t.hooks.chain("postConversion",i),t};var s=/^(<\/?(b|blockquote|code|del|dd|dl|dt|em|h1|h2|h3|i|kbd|li|ol|p|pre|s|sup|sub|strong|strike|ul)>|<(br|hr)\s?\/?>)$/i,o=/^(<a\shref="((https?|ftp):\/\/|\/)[-A-Za-z0-9+&@#\/%?=~_|!:,.;\(\)]+"(\stitle="[^"<>]+")?\s?>|<\/a>)$/i,a=/^(<img\ssrc="(https?:\/\/|\/)[-A-Za-z0-9+&@#\/%?=~_|!:,.;\(\)]+"(\swidth="\d{1,3}")?(\sheight="\d{1,3}")?(\salt="[^"<>]*")?(\stitle="[^"<>]*")?\s?\/?>)$/i})();