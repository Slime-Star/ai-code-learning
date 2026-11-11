import {Marked} from 'marked'
import hljs from 'highlight.js'
const escapeHtml=value=>String(value).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;')
const parser=new Marked({gfm:true,breaks:true,renderer:{
  html:()=>'',image:()=>'',
  code({text,lang}){const language=String(lang || '').split(/\s/)[0];return `<pre><code class="hljs">${hljs.getLanguage(language)?hljs.highlight(text,{language,ignoreIllegals:true}).value:escapeHtml(text)}</code></pre>`},
  link({href,text}){let url;try{url=new URL(href,window.location.origin)}catch{return escapeHtml(text)};if(!['http:','https:','mailto:'].includes(url.protocol))return escapeHtml(text);return `<a href="${escapeHtml(url.href)}" target="_blank" rel="noopener noreferrer">${escapeHtml(text)}</a>`}
}})
export function assistantMarkdown(content){return parser.parse(String(content || '').slice(0,50000).replace(/\n{3,}/g,'\n\n'))}
