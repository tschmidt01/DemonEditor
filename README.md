# DemonEditor

## Experimental version of Enigma2 channel and satellites list editor for GNU/Linux and MS Windows.
Experimental support of Neutrino-MP or others on the same basis (BPanther, etc).                                                   
Focused on the convenience of working in lists from the keyboard. The mouse is also fully supported (Drag and Drop etc)

## Note
This version is recommended only for users of fairly old systems or those who wish to try running this program on MS Windows.
The functionality and performance of this version may be very different from the main version!                           
**Not all features are supported and fully tested!**                                                                    

### Keyboard shortcuts:                                                                                                                
**Ctrl + X, C, V, Up, Down, PageUp, PageDown, Home, End, S, T, E, L, H, Space; Insert, Delete, F2, Enter, P.**                                                    
* **Insert** - copies the selected channels from the main list to the bouquet or inserts (creates) a new bouquet.                                     
* **Ctrl + X** - only in bouquet list. **Ctrl + C** - only in services list.                                                                 
Clipboard is **"rubber"**. There is an accumulation before the insertion!                                                              
* **Ctrl + E** - edit.                                                                                                                                                                                                                                                                                                                    
* **Ctrl + R, F2** - rename.                                                                                                                                                                                                                                                                                                                     
* **Ctrl + S, T** in Satellites edit tool for create satellite or transponder.                                                                 
* **Ctrl + L** - parental lock.                                                                                                          
* **Ctrl + H** - hide/skip.                                                                                                                                                                                                 
* **P** - enable/disable preview mode for IPTV in the bouquet list.                                                                                                 
* **Enter** - start play IPTV or other stream in the bouquet list.                                                      
* **Space** - select/deselect.                                                                                                                                                                                                                                                                                                           
* **Left/Right** - remove selection.                                                                                       
* **Ctrl + Up, Down, PageUp, PageDown, Home, End** - move selected items in the list.  
                                                                                                                                                                                                                                                                                                                                      
### Extra:
* Multiple selections in lists only with Space key (as in file managers).                                                                                                                                                                                                                                                                                                                                                                                                                                        
* Ability to import IPTV into bouquet (Neutrino WEBTV) from m3u files.                                                                                    
* Ability to download picons and update satellites (transponders) from web.                                                                                                                                                                                                                                                         
* Preview (playing)  IPTV or other streams directly from the bouquet list(should be installed VLC).     
                                         
### Minimum requirements:
Python >= **3.4** and GTK+ >= **3.10** with PyGObject bindings.

### Launching                                                                                                           
To start the program, in most cases it is enough to download the archive, unpack and run it by                                                   
double clicking on DemonEditor.desktop in the root directory, or launching from the console                                                           
with the command: ```./start.py```                                                                              
Extra folders can be deleted, excluding the *app* folder and root files like *DemonEditor.desktop* and *start.py*!      
                                                                                                                                                                  
### Note.
**Terrestrial(DVB-T/T2) and cable channels are supported(Enigma2 only) with limitation!** 

Main supported **lamedb** format is version **4**. Versions **3** and **5** has only experimental support!                                                                                                                                          
For version **3** is only read mode available. When saving, version **4** format is used instead! 
     
## For run on MS Windows
For correct operations with picons you can take "wget.exe" from here: https://eternallybored.org/misc/wget/                                                         
and "mogrify.exe" from portable Win32 static package here : https://www.imagemagick.org/script/download.php             
Or from other sources at your discretion.
       




