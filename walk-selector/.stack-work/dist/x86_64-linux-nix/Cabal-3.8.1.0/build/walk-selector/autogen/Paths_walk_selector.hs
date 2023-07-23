{-# LANGUAGE CPP #-}
{-# LANGUAGE NoRebindableSyntax #-}
{-# OPTIONS_GHC -fno-warn-missing-import-lists #-}
{-# OPTIONS_GHC -w #-}
module Paths_walk_selector (
    version,
    getBinDir, getLibDir, getDynLibDir, getDataDir, getLibexecDir,
    getDataFileName, getSysconfDir
  ) where


import qualified Control.Exception as Exception
import qualified Data.List as List
import Data.Version (Version(..))
import System.Environment (getEnv)
import Prelude


#if defined(VERSION_base)

#if MIN_VERSION_base(4,0,0)
catchIO :: IO a -> (Exception.IOException -> IO a) -> IO a
#else
catchIO :: IO a -> (Exception.Exception -> IO a) -> IO a
#endif

#else
catchIO :: IO a -> (Exception.IOException -> IO a) -> IO a
#endif
catchIO = Exception.catch

version :: Version
version = Version [0,1,0,0] []

getDataFileName :: FilePath -> IO FilePath
getDataFileName name = do
  dir <- getDataDir
  return (dir `joinFileName` name)

getBinDir, getLibDir, getDynLibDir, getDataDir, getLibexecDir, getSysconfDir :: IO FilePath




bindir, libdir, dynlibdir, datadir, libexecdir, sysconfdir :: FilePath
bindir     = "/home/isaac/repos/walk-selector/walk-selector/.stack-work/install/x86_64-linux-nix/378e914194bf2308522d3ba6d55fcf164c42796f5ef7dd043f5db02f023013ea/9.4.5/bin"
libdir     = "/home/isaac/repos/walk-selector/walk-selector/.stack-work/install/x86_64-linux-nix/378e914194bf2308522d3ba6d55fcf164c42796f5ef7dd043f5db02f023013ea/9.4.5/lib/x86_64-linux-ghc-9.4.5/walk-selector-0.1.0.0-1dqpqEcwPBt3YqiTvesyKu-walk-selector"
dynlibdir  = "/home/isaac/repos/walk-selector/walk-selector/.stack-work/install/x86_64-linux-nix/378e914194bf2308522d3ba6d55fcf164c42796f5ef7dd043f5db02f023013ea/9.4.5/lib/x86_64-linux-ghc-9.4.5"
datadir    = "/home/isaac/repos/walk-selector/walk-selector/.stack-work/install/x86_64-linux-nix/378e914194bf2308522d3ba6d55fcf164c42796f5ef7dd043f5db02f023013ea/9.4.5/share/x86_64-linux-ghc-9.4.5/walk-selector-0.1.0.0"
libexecdir = "/home/isaac/repos/walk-selector/walk-selector/.stack-work/install/x86_64-linux-nix/378e914194bf2308522d3ba6d55fcf164c42796f5ef7dd043f5db02f023013ea/9.4.5/libexec/x86_64-linux-ghc-9.4.5/walk-selector-0.1.0.0"
sysconfdir = "/home/isaac/repos/walk-selector/walk-selector/.stack-work/install/x86_64-linux-nix/378e914194bf2308522d3ba6d55fcf164c42796f5ef7dd043f5db02f023013ea/9.4.5/etc"

getBinDir     = catchIO (getEnv "walk_selector_bindir")     (\_ -> return bindir)
getLibDir     = catchIO (getEnv "walk_selector_libdir")     (\_ -> return libdir)
getDynLibDir  = catchIO (getEnv "walk_selector_dynlibdir")  (\_ -> return dynlibdir)
getDataDir    = catchIO (getEnv "walk_selector_datadir")    (\_ -> return datadir)
getLibexecDir = catchIO (getEnv "walk_selector_libexecdir") (\_ -> return libexecdir)
getSysconfDir = catchIO (getEnv "walk_selector_sysconfdir") (\_ -> return sysconfdir)



joinFileName :: String -> String -> FilePath
joinFileName ""  fname = fname
joinFileName "." fname = fname
joinFileName dir ""    = dir
joinFileName dir fname
  | isPathSeparator (List.last dir) = dir ++ fname
  | otherwise                       = dir ++ pathSeparator : fname

pathSeparator :: Char
pathSeparator = '/'

isPathSeparator :: Char -> Bool
isPathSeparator c = c == '/'
