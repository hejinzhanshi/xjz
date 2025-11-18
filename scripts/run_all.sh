set -e
if [ ! -d "$HOME/comp3014j" ]; then
  cd "$HOME"
  git clone https://csgitlab.ucd.ie/nima/comp3014j.git
fi
cd "$HOME/comp3014j"
ns cubicCode.tcl || true
ns yeahCode.tcl || true
ns renoCode.tcl || true
ns vegasCode.tcl || true
mkdir -p "$HOME/comp3014j/traces_drop"
cp *.tr "$HOME/comp3014j/traces_drop" || true
sed -i 's/DropTail/RED/g' cubicCode.tcl yeahCode.tcl renoCode.tcl vegasCode.tcl
ns cubicCode.tcl || true
ns yeahCode.tcl || true
ns renoCode.tcl || true
ns vegasCode.tcl || true
mkdir -p "$HOME/comp3014j/traces_red"
cp *.tr "$HOME/comp3014j/traces_red" || true
sed -i 's/RED/DropTail/g' cubicCode.tcl yeahCode.tcl renoCode.tcl vegasCode.tcl
sed -i 's/1000Mb/500Mb/g' cubicCode.tcl yeahCode.tcl renoCode.tcl vegasCode.tcl
ns cubicCode.tcl || true
ns yeahCode.tcl || true
ns renoCode.tcl || true
ns vegasCode.tcl || true
mkdir -p "$HOME/comp3014j/traces_sensitivity"
cp *.tr "$HOME/comp3014j/traces_sensitivity" || true
sed -i 's/500Mb/1000Mb/g' cubicCode.tcl yeahCode.tcl renoCode.tcl vegasCode.tcl
pip3 install -r "$HOME/xjz/requirements.txt"
pip3 install traceanalyzer
python3 "$HOME/xjz/analyser3.py" partA --traces-dir "$HOME/comp3014j/traces_drop" --out-dir "$HOME/comp3014j/analysis_partA"
python3 "$HOME/xjz/analyser3.py" partB --drop-dir "$HOME/comp3014j/traces_drop" --red-dir "$HOME/comp3014j/traces_red" --out-dir "$HOME/comp3014j/analysis_partB"
cp "$HOME/comp3014j"/reno*.tr "$HOME/comp3014j/partC_run1.tr" || true
ns renoCode.tcl || true
cp "$HOME/comp3014j"/reno*.tr "$HOME/comp3014j/partC_run2.tr" || true
ns renoCode.tcl || true
cp "$HOME/comp3014j"/reno*.tr "$HOME/comp3014j/partC_run3.tr" || true
ns renoCode.tcl || true
cp "$HOME/comp3014j"/reno*.tr "$HOME/comp3014j/partC_run4.tr" || true
ns renoCode.tcl || true
cp "$HOME/comp3014j"/reno*.tr "$HOME/comp3014j/partC_run5.tr" || true
python3 "$HOME/xjz/analyser3.py" partC --traces "$HOME/comp3014j/partC_run1.tr" "$HOME/comp3014j/partC_run2.tr" "$HOME/comp3014j/partC_run3.tr" "$HOME/comp3014j/partC_run4.tr" "$HOME/comp3014j/partC_run5.tr" --out-dir "$HOME/comp3014j/analysis_partC"
if [ -f "$HOME/comp3014j/analyser2.py" ]; then
  python3 "$HOME/comp3014j/analyser2.py"
fi
if [ -f "$HOME/comp3014j/analyser.py" ]; then
  python3 "$HOME/comp3014j/analyser.py"
fi
