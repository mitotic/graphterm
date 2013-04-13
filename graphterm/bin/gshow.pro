pro gshow, command, overwrite=overwrite, xsize=xsize, ysize=ysize, _EXTRA=_EXTRA
  esc = string(27B)
  lf = string(10B)
  gterm_code = 1155
  cookie = getenv("GRAPHTERM_COOKIE")
  if (cookie eq "") then cookie = getenv("LC_GRAPHTERM_COOKIE")
  if (cookie eq "") then message, "No graphterm cookie"

  esc_prefix = esc+'[?'+strtrim(gterm_code,2)+';'+strtrim(cookie,2)+'h'
  esc_suffix = esc+'[?'+strtrim(gterm_code,2)+'l'
  ;;print, esc_prefix, '<b>Hello</b> World!', esc_suffix, format='(a,a,a,$)'

  if(not keyword_set(overwrite)) then overwrite=0
  if(not keyword_set(xsize)) then xsize=640
  if(not keyword_set(ysize)) then ysize=480

  set_plot, 'z'
  device, z_buffering=1, set_resolution=[xsize, ysize], _EXTRA=_EXTRA
  tvlct, r,g,b, /get

  result = execute(command)

  if (not result) then message, "Error in executing command"

  img = tvrd()

  image2d = bytarr(3, xsize, ysize)
  image2d(0,*,*) = r[img]
  image2d(1,*,*) = g[img]
  image2d(2,*,*) = b[img]

  blob_id = strtrim(long64(1e12 * randomu(undef)), 2)
  ;;filename = filepath('gshow'+blob_id+'.png', /tmp)
  filename = filepath('gshow'+blob_id+'.png', root_dir=".")

  write_png, filename, image2d, r, g, b

  png_data = read_binary(filename)
  png_b64 = idl_base64(png_data)
  png_size = size(png_data)
  content_type = 'image/png'
  content = '<!--gterm data blob=' +strtrim(blob_id,2)+'-->'+content_type+';base64,'+png_b64
  print, esc_prefix, content, esc_suffix, format='(a,a,a,$)'

  params = ""
  if (overwrite) then params = "overwrite=yes"
  img_html = '<!--gterm pagelet display=block blob='+strtrim(blob_id,2)+' '+params+'--><div class="gterm-blockhtml"><img class="gterm-blockimg" src="/blob/local/'+strtrim(blob_id,2)+'"></div>'

  print, esc_prefix, img_html, esc_suffix, format='(a,a,a,$)'
end
