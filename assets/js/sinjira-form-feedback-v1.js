/* Aide locale à la validation native. Aucun accès aux valeurs saisies. */
(function(){
  'use strict';
  function initialize(){
    var form=document.querySelector('form[data-login-form],form[data-signup-form],form[data-forgot-form],form[data-reset-form]');
    if(!form||form.hasAttribute('data-sinjira-feedback-ready'))return;
    form.setAttribute('data-sinjira-feedback-ready','');
    var active=new Map(),sequence=0;
    function message(field){
      var v=field.validity;
      if(v.valueMissing)return 'Ce champ est obligatoire.';
      if(v.typeMismatch)return field.type==='email'?'Entrez une adresse courriel valide.':'Vérifiez le format demandé.';
      if(v.tooShort)return 'La saisie est trop courte. Vérifiez la longueur minimale.';
      if(v.tooLong)return 'La saisie est trop longue.';
      if(v.rangeUnderflow||v.rangeOverflow||v.stepMismatch)return 'Vérifiez les limites indiquées pour ce champ.';
      if(v.patternMismatch||v.badInput)return 'Vérifiez le format demandé.';
      return 'Vérifiez ce champ avant de continuer.';
    }
    function eligible(field){
      return field&&field.matches&&field.matches('input,select,textarea')&&field.willValidate;
    }
    function clear(field){
      var entry=active.get(field);
      if(!entry)return;
      var ids=(field.getAttribute('aria-describedby')||'').split(/\s+/).filter(function(id){return id&&id!==entry.note.id;});
      if(ids.length)field.setAttribute('aria-describedby',ids.join(' '));
      else field.removeAttribute('aria-describedby');
      if(entry.previousInvalid===null)field.removeAttribute('aria-invalid');
      else field.setAttribute('aria-invalid',entry.previousInvalid);
      field.removeAttribute('data-sinjira-invalid');
      entry.note.remove();
      active.delete(field);
    }
    function show(field){
      if(!eligible(field))return;
      var entry=active.get(field);
      if(!entry){
        var note=document.createElement('span'),id;
        do{id='sinjira-validation-'+(++sequence);}while(document.getElementById(id));
        note.id=id;note.className='sinjira-field-error';
        entry={note:note,previousInvalid:field.getAttribute('aria-invalid')};
        active.set(field,entry);
        field.insertAdjacentElement('afterend',note);
        var described=field.getAttribute('aria-describedby')||'';
        field.setAttribute('aria-describedby',(described+' '+id).trim());
      }
      entry.note.textContent=message(field);
      field.setAttribute('aria-invalid','true');
      field.setAttribute('data-sinjira-invalid','');
    }
    function refresh(event){
      var field=event.target;
      if(!active.has(field))return;
      if(!eligible(field)||field.validity.valid)clear(field);
      else show(field);
    }
    form.addEventListener('invalid',function(event){show(event.target);},true);
    form.addEventListener('input',refresh);
    form.addEventListener('change',refresh);
    form.addEventListener('reset',function(event){
      // Respecter une réinitialisation annulée par un autre gestionnaire.
      Promise.resolve().then(function(){if(!event.defaultPrevented)active.forEach(function(_,field){clear(field);});});
    });
    if(typeof MutationObserver!=='undefined'){
      new MutationObserver(function(){
        active.forEach(function(_,field){if(!form.contains(field)||!eligible(field))clear(field);});
      }).observe(form,{subtree:true,childList:true,attributes:true,attributeFilter:['disabled','required','type']});
    }
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
  else initialize();
}());
