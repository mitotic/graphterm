;; Demo for embedded graphics using NCL

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"  ; Load the NCL file that contains the
                                                          ; gsn_* functions used below.
begin
  x = new(9,float)  ; Define two 1D arrays of 9 elements each.
  y = new(9,float)

  x = (/10.,20.,30.,40.,50.,60.,70.,80.,90./)
  y = (/0.,0.71,1.,0.7,0.002,-0.71,-1.,-0.71,-0.003/)
  y2 = (/(/0., 0.7, 1., 0.7, 0., -0.7, -1., -0.7, 0./),\
         (/2., 2.7, 3., 2.7, 2.,  1.3,  1.,  1.3, 2./),\
         (/4., 4.7, 5., 4.7, 4.,  3.3,  3.,  3.3, 4./)/)

  wks_type = "png"
  wks_type@wkWidth = 500
  wks_type@wkHeight = 300 
  wks = gsn_open_wks(wks_type,"ncloutput")  ; Open an PNG workstation.

  resources                    = True          ; Indicate you want to
                                               ; set some resources.
  
  resources@xyLineColors        = (/2,3,4/)    ; Define line colors.
  resources@xyLineThicknesses   = (/1.,2.,5./) ; Define line thicknesses 
                                               ; (1.0 is the default).
  
  plot = gsn_xy(wks,x,y2,resources)            ; Draw an XY plot.

  system("./gimg.sh ncloutput.png")    ; Display it inline
  delete(plot)                         ; Clean up.
end
