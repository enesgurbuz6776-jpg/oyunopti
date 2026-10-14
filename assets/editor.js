(()=>{
'use strict';
const $=id=>document.getElementById(id);
const video=$('sourceVideo'),canvas=$('previewCanvas'),ctx=canvas.getContext('2d',{alpha:false});
const input=$('videoInput'),drop=$('dropZone'),stage=$('canvasHolder'),empty=$('emptyStage');
const playButton=$('playPause'),seek=$('seekBar'),startRange=$('trimStart'),endRange=$('trimEnd');
const exportButton=$('exportButton'),thumbnailButton=$('thumbnailButton'),download=$('downloadLink');
const state={file:null,url:null,downloadUrl:null,ratio:'9:16',start:0,end:0,duration:0,exporting:false,recorder:null,stream:null,done:false,quality:'hd',mime:''};
let audioCtx=null,mediaAudioSource=null,previewGain=null,recordGain=null,recordDest=null,lastTick=0,exportTimer=null;
const RECORDER_TYPES=['video/mp4;codecs=avc1.42E01E,mp4a.40.2','video/mp4;codecs=avc1.42E01E','video/mp4','video/webm;codecs=vp9,opus','video/webm;codecs=vp8,opus','video/webm'];
const support=()=>{if(!window.MediaRecorder||!HTMLCanvasElement.prototype.captureStream)return '';return RECORDER_TYPES.find(t=>MediaRecorder.isTypeSupported(t))||''};
const time=t=>{const s=Math.max(0,Number(t)||0);const mins=Math.floor(s/60),secs=Math.floor(s%60),hund=Math.floor((s%1)*10);return `${String(mins).padStart(2,'0')}:${String(secs).padStart(2,'0')}.${hund}`};
const pretty=n=>n<1024*1024?`${(n/1024).toFixed(1)} KB`:`${(n/1048576).toFixed(1)} MB`;
const status=(message,kind='')=>{const el=$('exportStatus');el.textContent=message;el.className='status'+(kind?' '+kind:'');el.hidden=!message};
const showProgress=n=>{const p=$('exportProgress');p.hidden=false;$('progressFill').style.width=`${Math.max(0,Math.min(100,n))}%`};
const hideDownload=()=>{const box=$('downloadBox');box.hidden=true;if(state.downloadUrl){URL.revokeObjectURL(state.downloadUrl);state.downloadUrl=null}};
const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
const size=()=>{const hd=$('quality').value==='hd';if(state.ratio==='9:16')return hd?[720,1280]:[432,768];if(state.ratio==='1:1')return hd?[720,720]:[540,540];return hd?[1280,720]:[768,432]};
const updateResolution=()=>{const [w,h]=size();if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h}const segment=Math.max(0,state.end-state.start);const s=Number($('speed').value)||1;const mime=support();$('exportSummary').textContent=`${w} × ${h} • ${(segment/s).toFixed(1)} sec • ${mime.startsWith('video/mp4')?'MP4':mime?'WebM':'Export unsupported'}`;$('ratioBadge').textContent=state.ratio};
const filterValue=()=>({normal:'none',vibrant:'saturate(1.7) contrast(1.10)',cinematic:'contrast(1.14) saturate(0.82) brightness(0.91)',mono:'grayscale(1) contrast(1.10)',warm:'sepia(0.24) saturate(1.23)'}[$('filter').value]||'none');
function wrapText(text,maxWidth){const raw=text.split(/\r?\n/),lines=[];for(const part of raw){const words=part.split(/\s+/).filter(Boolean);if(!words.length){lines.push('');continue}let line='';for(const word of words){const next=line?line+' '+word:word;if(ctx.measureText(next).width<=maxWidth){line=next;continue}if(line){lines.push(line);line=''}if(ctx.measureText(word).width>maxWidth){let piece='';for(const c of [...word]){if(ctx.measureText(piece+c).width>maxWidth&&piece){lines.push(piece);piece=c}else piece+=c}line=piece}else line=word}if(line)lines.push(line)}return lines.slice(0,8)}
function renderFrame(){
 const w=canvas.width,h=canvas.height;ctx.fillStyle=$('background').value;ctx.fillRect(0,0,w,h);
 if(state.file && video.readyState>=2 && video.videoWidth>0){const sw=video.videoWidth,sh=video.videoHeight;const cover=$('fitMode').value==='cover';const scale=cover?Math.max(w/sw,h/sh):Math.min(w/sw,h/sh);const dw=sw*scale,dh=sh*scale;ctx.save();ctx.filter=filterValue();ctx.drawImage(video,(w-dw)/2,(h-dh)/2,dw,dh);ctx.restore()}
 const overlay=$('overlayText').value.trim();if(overlay&&state.file){const base=Math.min(w,h);const fontSize=Math.round(Number($('textSize').value)*(base/720));ctx.save();ctx.textAlign='center';ctx.textBaseline='middle';ctx.font=`800 ${fontSize}px Arial,Helvetica,sans-serif`;ctx.lineJoin='round';const lines=wrapText(overlay,w*.88),lh=fontSize*1.15,blockH=lh*lines.length;let center=h*.8;if($('textPosition').value==='top')center=h*.17;if($('textPosition').value==='center')center=h*.5;const startY=clamp(center-(blockH-lh)/2,h*.045,h*.955-(blockH-lh));ctx.lineWidth=Math.max(3,fontSize*.16);ctx.strokeStyle='#111015';ctx.shadowColor='#0009';ctx.shadowBlur=fontSize*.19;ctx.fillStyle=$('textColor').value;for(let i=0;i<lines.length;i++){const y=startY+i*lh;ctx.strokeText(lines[i],w/2,y,w*.92);ctx.fillText(lines[i],w/2,y,w*.92)}ctx.restore()}
}
function timeline(){const d=Math.max(.01,state.duration),cur=clamp(video.currentTime||state.start,0,d);$('startLabel').textContent=time(state.start);$('endLabel').textContent=time(state.end);$('trimHint').textContent=`Selected ${(Math.max(0,state.end-state.start)).toFixed(1)} sec • ${time(state.start)} → ${time(state.end)}`;$('trackBar').style.setProperty('--start',`${(state.start/d*100).toFixed(3)}%`);$('trackBar').style.setProperty('--end',`${(state.end/d*100).toFixed(3)}%`);$('trackBar').style.setProperty('--position',`${(cur/d*100).toFixed(3)}%`)}
function updatePlayhead(){const d=state.duration||0,cur=video.currentTime||0;$('currentTime').textContent=time(cur);seek.value=String(clamp(cur,0,d));playButton.textContent=video.paused?'▶':'❚❚';timeline()}
function stopAtEnd(){if(!state.file)return;if(state.exporting&&(video.ended||video.currentTime>=state.end-.035)){finishRecording();return}if(!video.paused&&video.currentTime>=state.end-.035){video.pause();video.currentTime=state.start;updatePlayhead()}}
function loop(now){requestAnimationFrame(loop);if(now-lastTick<33)return;lastTick=now;if(state.file){renderFrame();updatePlayhead();stopAtEnd();if(state.exporting){let progress=(video.currentTime-state.start)/Math.max(.01,state.end-state.start);showProgress(progress*100);$('exportStatus').textContent=`Recording locally… ${Math.max(0,Math.floor(progress*100))}% · Keep this tab open.`}}}
requestAnimationFrame(loop);
const allControls=[...document.querySelectorAll('input,select,textarea,button')].filter(n=>n!==input);function lockControls(lock){state.exporting=lock;for(const el of allControls){if(lock){el.dataset.oldDisabled=el.disabled?'1':'0';el.disabled=true}else{el.disabled=el.dataset.oldDisabled==='1';delete el.dataset.oldDisabled}}drop.style.pointerEvents=lock?'none':'auto';exportButton.textContent=lock?'⏳ Recording…':'⬇ Export video'}
function setAudioMute(){if(previewGain){previewGain.gain.value=$('muteAudio').checked?0:1;if(recordGain)recordGain.gain.value=$('muteAudio').checked?0:1;video.muted=false}else{video.muted=$('muteAudio').checked}}
async function ensureAudio(){
 if(audioCtx){if(audioCtx.state==='suspended')await audioCtx.resume();return Boolean(recordDest)}
 const AudioCtx=window.AudioContext||window.webkitAudioContext;if(!AudioCtx)return false;
 try{audioCtx=new AudioCtx();mediaAudioSource=audioCtx.createMediaElementSource(video);previewGain=audioCtx.createGain();recordGain=audioCtx.createGain();recordDest=audioCtx.createMediaStreamDestination();mediaAudioSource.connect(previewGain);previewGain.connect(audioCtx.destination);mediaAudioSource.connect(recordGain);recordGain.connect(recordDest);setAudioMute();await audioCtx.resume();return true}catch(e){console.warn('Audio routing unavailable:',e);return false}
}
async function openFile(file){
 if(!file||state.exporting)return;if(!file.type.startsWith('video/')&&!/\.(mp4|webm|mov|m4v|ogg)$/i.test(file.name)){status('Select a valid video file.','error');return}
 if(state.url)URL.revokeObjectURL(state.url);hideDownload();state.file=file;state.done=false;state.start=0;state.end=0;state.duration=0;
 const url=URL.createObjectURL(file);state.url=url;video.pause();video.removeAttribute('src');video.load();video.src=url;video.playbackRate=Number($('speed').value);setAudioMute();
 $('fileName').textContent=file.name;$('fileDetail').textContent=`${pretty(file.size)} • Reading metadata…`;$('fileMeta').hidden=false;status('Loading video file…');
}
video.addEventListener('loadedmetadata',()=>{const duration=video.duration;if(!Number.isFinite(duration)||duration<=0){status('Video has no usable duration. Try another file.','error');return}state.file=state.file || input.files?.[0] || window._droppedFile;state.duration=duration;state.end=duration;const max=duration.toFixed(3);startRange.max=max;endRange.max=max;seek.max=max;startRange.value='0';endRange.value=String(duration);seek.value='0';for(const el of [startRange,endRange,seek,playButton,exportButton,thumbnailButton])el.disabled=false;
 $('fileDetail').textContent=`${time(duration)} • ${video.videoWidth} × ${video.videoHeight}`;$('totalTime').textContent=time(duration);$('timelineDuration').textContent=time(duration);stage.classList.add('ready');empty.hidden=true;updateResolution();timeline();$('previewStatus').textContent='Ready to edit';status('Loaded! Set your in/out points, then press Export.','success');video.currentTime=0});
video.addEventListener('loadeddata',renderFrame);video.addEventListener('ended',()=>{if(state.exporting)finishRecording();else updatePlayhead()});
video.addEventListener('error',()=>{if(state.url){state.file=null;status('This browser cannot play this file or codec. Try a standard MP4 (H.264) or WebM video.','error');exportButton.disabled=true;playButton.disabled=true;thumbnailButton.disabled=true}});
input.addEventListener('change',()=>{const f=input.files?.[0];if(f){state.file=f;openFile(f)}});
for(const name of ['dragenter','dragover'])drop.addEventListener(name,e=>{e.preventDefault();drop.classList.add('drag')});for(const name of ['dragleave','drop'])drop.addEventListener(name,e=>{e.preventDefault();drop.classList.remove('drag')});drop.addEventListener('drop',e=>{const f=e.dataTransfer?.files?.[0];if(f){window._droppedFile=f;state.file=f;openFile(f)}});
playButton.addEventListener('click',async()=>{if(!state.file||state.exporting)return;try{if(video.paused){if(video.currentTime<state.start||video.currentTime>=state.end-.05)video.currentTime=state.start;await video.play()}else video.pause();updatePlayhead()}catch(e){status('Could not play this video: '+e.message,'error')}});
seek.addEventListener('input',()=>{if(state.exporting)return;video.currentTime=clamp(Number(seek.value),state.start,Math.max(state.start,state.end-.03));renderFrame()});
startRange.addEventListener('input',()=>{const value=Number(startRange.value);state.start=Math.min(value,state.end-.15);startRange.value=String(state.start);if(video.currentTime<state.start||video.currentTime>=state.end)video.currentTime=state.start;updateResolution();timeline()});
endRange.addEventListener('input',()=>{const value=Number(endRange.value);state.end=Math.max(value,state.start+.15);endRange.value=String(state.end);if(video.currentTime>state.end)video.currentTime=state.start;updateResolution();timeline()});
for(const b of document.querySelectorAll('[data-ratio]'))b.addEventListener('click',()=>{state.ratio=b.dataset.ratio;document.querySelectorAll('[data-ratio]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));updateResolution();renderFrame()});
$('quality').addEventListener('change',()=>{updateResolution();renderFrame()});$('speed').addEventListener('change',()=>{video.playbackRate=Number($('speed').value);updateResolution()});$('muteAudio').addEventListener('change',setAudioMute);
for(const id of ['fitMode','background','overlayText','textPosition','textSize','textColor','filter'])$(id).addEventListener('input',()=>{if(id==='textSize')$('textSizeValue').textContent=$('textSize').value;renderFrame()});
async function seekTo(t){if(Math.abs(video.currentTime-t)<.03){renderFrame();return}await new Promise((resolve,reject)=>{let timeout=setTimeout(()=>{cleanup();resolve()},2500);function cleanup(){clearTimeout(timeout);video.removeEventListener('seeked',done);video.removeEventListener('error',fail)}function done(){cleanup();resolve()}function fail(){cleanup();reject(Error('Could not seek the video.'))}video.addEventListener('seeked',done,{once:true});video.addEventListener('error',fail,{once:true});video.currentTime=t})}
const nativeMime=support();if(!nativeMime){$('previewStatus').textContent='Export may not be supported in this browser'}
async function exportVideo(){
 if(!state.file||state.exporting)return;if(!window.MediaRecorder||!canvas.captureStream){status('This browser does not support local video recording. Try a current Chrome or Edge browser.','error');return}
 if(!support()){status('No supported video recording format was detected in this browser.','error');return}
 hideDownload();video.pause();try{await seekTo(state.start)}catch(e){status(e.message,'error');return}renderFrame();
 let recorder=null;let stream=null;let mime=support();lockControls(true);status('Preparing local export…');showProgress(0);let recorded=[];
 try{
   const hasAudio=await ensureAudio();setAudioMute();const videoStream=canvas.captureStream(30);const videoTrack=videoStream.getVideoTracks()[0];if(!videoTrack)throw Error('Unable to capture video frames.');let tracks=[videoTrack];if(hasAudio){tracks.push(...recordDest.stream.getAudioTracks())}stream=new MediaStream(tracks);
   try{recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:5000000,audioBitsPerSecond:128000})}catch(e){if(hasAudio){stream=new MediaStream([videoTrack]);recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:5000000})}else throw e}
   state.recorder=recorder;state.stream=stream;state.mime=mime;
   recorder.addEventListener('dataavailable',e=>{if(e.data?.size>0)recorded.push(e.data)});
   recorder.addEventListener('stop',()=>{if(exportTimer){clearTimeout(exportTimer);exportTimer=null}video.pause();lockControls(false);for(const t of stream.getTracks())if(t!==recordDest?.stream.getAudioTracks()[0])t.stop();state.recorder=null;state.stream=null;$('exportProgress').hidden=true;
    if(!recorded.length){status('Nothing was recorded. Try a shorter clip or another browser.','error');return}const data=new Blob(recorded,{type:recorder.mimeType||mime});if(data.size<1024){status('The exported file appears empty. Try again.','error');return}const ext=(data.type||mime).includes('mp4')?'mp4':'webm';state.downloadUrl=URL.createObjectURL(data);download.href=state.downloadUrl;download.download='cutlance-'+Date.now()+'.'+ext;$('downloadMeta').textContent=`${pretty(data.size)} · ${ext.toUpperCase()} · ${time((state.end-state.start)/Number($('speed').value))} · No watermark`;$('downloadBox').hidden=false;status('Your video is ready! Click Download your video.','success')});
   recorder.addEventListener('error',e=>{console.error(e);status('Recording failed. Try a shorter clip or reduce resolution.','error');finishRecording()});
   await audioCtx?.resume();recorder.start(250);video.currentTime=state.start;await video.play();
   exportTimer=setTimeout(()=>{if(state.exporting){status('Export ended due to browser time limit. Try a shorter section.','error');finishRecording()}},Math.max(12000,(state.end-state.start)/Number($('speed').value)*1000+11000));
   status('Recording locally. Keep this tab open.','');
 }catch(e){console.error(e);if(recorder?.state==='recording')recorder.stop();else{lockControls(false);$('exportProgress').hidden=true}if(stream)for(const t of stream.getVideoTracks())t.stop();status('Export could not start: '+e.message,'error')}
}
function finishRecording(){if(!state.exporting)return;video.pause();const r=state.recorder;if(r&&r.state!=='inactive'){try{r.requestData()}catch(e){}try{r.stop()}catch(e){console.warn(e)}}else{lockControls(false);$('exportProgress').hidden=true}if(exportTimer){clearTimeout(exportTimer);exportTimer=null}}
exportButton.addEventListener('click',exportVideo);
thumbnailButton.addEventListener('click',()=>{if(!state.file||state.exporting)return;renderFrame();canvas.toBlob(blob=>{if(!blob){status('Could not save this frame.','error');return}const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='cutlance-thumbnail.png';a.click();setTimeout(()=>URL.revokeObjectURL(url),30000);status('Thumbnail saved as PNG.','success')},'image/png')});
window.addEventListener('beforeunload',e=>{if(state.exporting){e.preventDefault();e.returnValue=''}});
window.addEventListener('pagehide',()=>{if(state.url)URL.revokeObjectURL(state.url);if(state.downloadUrl)URL.revokeObjectURL(state.downloadUrl);if(audioCtx)audioCtx.close()});
const heights=[22,39,62,34,71,90,56,29,48,86,100,80,40,60,33,67,89,56,37,64,76,92,54,31,59,85,51,75,34,68,98,64,43,87,76,52,93,39,62,80,47,74,96,59,35,62,81,51];$('trackBars').innerHTML=heights.map(h=>`<i style="--h:${h}%"></i>`).join('');
updateResolution();
})();
