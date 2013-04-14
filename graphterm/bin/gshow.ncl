;; Demo for embedded graphics using NCL

load "$NCARG_ROOT/lib/ncarg/nclscripts/csm/gsn_code.ncl"  ; Load the NCL file that contains the
                                                          ; gsn_* functions used below.
begin
  x = new(9,float)  ; Define two 1D arrays of 9 elements each.
  y = new(9,float)

  x = (/10.,20.,30.,40.,50.,60.,70.,80.,90./)
  y = (/0.,0.71,1.,0.7,0.002,-0.71,-1.,-0.71,-0.003/)

  wks = gsn_open_wks("png","ncloutput")  ; Open an PNG workstation.

  plot = gsn_xy(wks,x,y,False)         ; Draw an XY plot with 1 curve.
  system("./gimg.sh ncloutput.png")    ; Display it inline
  delete(plot)                         ; Clean up.
end
