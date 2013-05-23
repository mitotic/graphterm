pro gshow, command, v, invert=invert, overwrite=overwrite, xsize=xsize, ysize=ysize, _EXTRA=_EXTRA
  ;; Derived from http://moonlets.org/Code/plot2png.pro
  ;; v is a structure for use in the command.
  ;; Example: gshow,'plot,v.x,v.y', {x:[1,2], y:[5,9]}, /invert
  esc = string(27B)
  lf = string(10B)
  gterm_code = 1155
  cookie = getenv("GTERM_COOKIE")
  if (cookie eq "") then cookie = getenv("LC_GTERM_COOKIE")
  if (cookie eq "") then message, "No graphterm cookie"

  esc_prefix = esc+'[?'+strtrim(gterm_code,2)+';'+strtrim(cookie,2)+'h'
  esc_suffix = esc+'[?'+strtrim(gterm_code,2)+'l'
  ;;print, esc_prefix, '<b>Hello</b> World!', esc_suffix, format='(a,a,a,$)'

  if (not keyword_set(overwrite)) then overwrite=0
  if (not keyword_set(xsize)) then xsize=400
  if (not keyword_set(ysize)) then ysize=300

  old_dev = !d.name

  set_plot, 'z'
  device, z_buffering=1, set_resolution=[xsize, ysize], _EXTRA=_EXTRA

  ;; Color table
  tvlct, r, g, b, /get

  if (keyword_set(invert)) then begin
    tvlct, r, g, b, /get
    tvlct, Reverse(r), Reverse(g), Reverse(b)
    temcolor = !P.Color
    !P.Color = !P.Background
    !P.Background = temcolor
  endif

  result = execute(command)

  if (not result) then begin
    set_plot, old_dev
    message, "Error in executing command: "+command
  endif

  img = tvrd()

  ;; Revert to saved device
  set_plot, old_dev

  image2d = bytarr(3, xsize, ysize)
  image2d[0,*,*] = r[img]
  image2d[1,*,*] = g[img]
  image2d[2,*,*] = b[img]

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
  img_html = '<!--gterm pagelet display=block blob='+strtrim(blob_id,2)+' '+params+'--><div class="gterm-blockhtml"><img class="gterm-blockimg" src="/_blob/local/'+strtrim(blob_id,2)+'"></div>'

  print, esc_prefix, img_html, esc_suffix, format='(a,a,a,$)'
end
