import { Routes } from '@angular/router';
import { CanvasAspectsComponent } from './containers/canvas-aspects/canvas-aspects.component';

export const routes: Routes = [
  {
    path: 'build',
    component: CanvasAspectsComponent
  },
  {
    path: 'about',
    component: CanvasAspectsComponent
  },
  {
    path: '',
    redirectTo: '/build',
    pathMatch: 'full'
  },
  {
    path: '**',
    redirectTo: '/build',
    pathMatch: 'full'
  }
];
