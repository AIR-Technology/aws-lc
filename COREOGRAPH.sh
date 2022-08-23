rm -rf build && mkdir build 
cmake -Bbuild -DCMAKE_C_FLAGS="-fPIC" -DCMAKE_BUILD_TYPE=release -DCMAKE_INSTALL_PREFIX=aws-lc-install -DBUILD_SHARED_LIBS=1 .
cmake --build build --config Release --target install -j $(nproc)

