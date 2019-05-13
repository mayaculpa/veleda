import { Routes } from '@angular/router';
import { CanvasAspectsComponent } from './containers/canvas-aspects/canvas-aspects.component';
import { FloorPlannerComponent } from './containers/floor-planner/floor-planner.component';

export const routes: Routes = [
  {
    path: 'floor-planner',
    component: FloorPlannerComponent
  },
  {
    path: 'canvas-aspects',
    component: CanvasAspectsComponent
  },
  {
    path: 'about',
    component: CanvasAspectsComponent
  },
  {
    path: '',
    redirectTo: '/canvas-aspects',
    pathMatch: 'full'
  },
  {
    path: '**',
    redirectTo: '/canvas-aspects',
    pathMatch: 'full'
  }
];
