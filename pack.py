from feanor import BaseBuilder

class Builder(BaseBuilder):
    def Setup(self):
        self.addDirectory('src', 'src/diagramTool')
        self.addAndReplaceByPackageVersion('pyproject.toml')
        self.addFile('Readme.md')
        self.addFile('example.svg')
        
        self.venv().install('build')
        
    def Build(self):
        self.venv().runModule(f'build --outdir {self.distDir}')