# Maintainer: Jürg Rechsteiner <jrechsteiner@bluewin.ch>
pkgname=vostiraview
pkgver=1.72
pkgrel=1
pkgdesc="Bildbetrachter mit Bearbeitungsfunktionen (PyQt6)"
arch=('any')
url="https://computer-experte.ch"
license=('GPL-3.0-or-later')
depends=('python' 'python-pyqt6' 'python-pillow')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("$pkgname-$pkgver.tar.gz::https://github.com/wergosam/vostiraview/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$pkgname-$pkgver"
  python -m build --wheel --no-isolation
}

package() {
  cd "$pkgname-$pkgver"
  python -m installer --destdir="$pkgdir" dist/*.whl

  # Icon
  install -Dm644 vostiraview_icon.svg \
    "$pkgdir/usr/share/icons/hicolor/scalable/apps/$pkgname.svg"

  # Lizenz
  install -Dm644 LICENSE \
    "$pkgdir/usr/share/licenses/$pkgname/LICENSE"

  # Desktop-Datei
  install -d "$pkgdir/usr/share/applications"
  cat > "$pkgdir/usr/share/applications/$pkgname.desktop" << EOF
[Desktop Entry]
Name=VostiraView
Comment=Bildbetrachter mit Bearbeitungsfunktionen
Exec=vostiraview
Icon=vostiraview
Terminal=false
Type=Application
Categories=Graphics;Viewer;Photography;
StartupWMClass=VostiraView
EOF
}
