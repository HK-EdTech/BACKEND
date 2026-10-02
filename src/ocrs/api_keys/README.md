# This directory contains API keys for OCR services

For pre-processing of the gcv.json, we need to:
` ! base64 < /Users/miltonchow/Downloads/fluid-axe-4xxxxxxxx.json | tr -d '\n' | pbcopy`

 - ! — runs the command in your terminal session so the output lands here in the chat with antrohpic                                                                                                     
  - -i — tells base64 the input is a file (instead of reading from keyboard)                                                                                                               
  - tr -d '\n' — removes all newlines from the output so it's one long single line (GitHub secrets need this)                                                                              
  - pbcopy — pipes the result straight to your clipboard (Mac only), so you can just Cmd+V into GitHub        

  The generate an encrpted json as base64 string and copies to clipboard directly